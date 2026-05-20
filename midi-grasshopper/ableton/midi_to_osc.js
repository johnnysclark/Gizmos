// Node-for-Max script used by MidiToOSC.amxd.
//
// Receives MIDI events from the Max patcher and emits OSC over UDP.
// Live 11+ ships Node for Max with Max for Live, so no separate
// install is needed. There are no npm dependencies beyond `max-api`,
// which Max for Live provides at runtime.
//
// Patcher messages this script accepts (case sensitive):
//   note <note> <velocity 0..127>
//   noteoff <note>
//   cc <value 0..127> <controller#>
//   bend <value -8192..8191>
//   aftertouch <value 0..127>
//   host <ip>            -- change UDP target host
//   port <int>           -- change UDP target port
//   status               -- emit current target + last sent
//
// Outlet messages (Node → patcher):
//   ["target", "127.0.0.1:7000"]
//   ["last",   "/cc/1 [0.512]"]
//   ["error",  "<message>"]

const maxApi = require('max-api');
const dgram = require('dgram');

const target = { host: '127.0.0.1', port: 7000 };
const sock = dgram.createSocket('udp4');
let lastSent = '(none yet)';
let lastNote = null;

function pad4(buf) {
  const pad = (4 - (buf.length % 4)) % 4;
  return pad ? Buffer.concat([buf, Buffer.alloc(pad)]) : buf;
}

function oscString(s) {
  return pad4(Buffer.concat([Buffer.from(s, 'utf8'), Buffer.from([0])]));
}

function encode(address, args) {
  let tags = ',';
  const parts = [];
  for (const a of args) {
    if (a === true) { tags += 'T'; continue; }
    if (a === false) { tags += 'F'; continue; }
    if (a === null) { tags += 'N'; continue; }
    if (typeof a === 'number') {
      if (Number.isInteger(a)) {
        tags += 'i';
        const b = Buffer.alloc(4);
        b.writeInt32BE(a | 0, 0);
        parts.push(b);
      } else {
        tags += 'f';
        const b = Buffer.alloc(4);
        b.writeFloatBE(a, 0);
        parts.push(b);
      }
    } else if (typeof a === 'string') {
      tags += 's';
      parts.push(oscString(a));
    }
  }
  return Buffer.concat([oscString(address), oscString(tags), ...parts]);
}

function send(address, ...args) {
  const pkt = encode(address, args);
  sock.send(pkt, 0, pkt.length, target.port, target.host, (err) => {
    if (err) {
      maxApi.outlet(['error', err.message]);
    }
  });
  lastSent = address + ' ' + JSON.stringify(args);
  maxApi.outlet(['last', lastSent]);
}

maxApi.addHandler('host', (h) => {
  target.host = String(h);
  maxApi.outlet(['target', target.host + ':' + target.port]);
});

maxApi.addHandler('port', (p) => {
  target.port = Number(p) | 0;
  maxApi.outlet(['target', target.host + ':' + target.port]);
});

maxApi.addHandler('status', () => {
  maxApi.outlet(['target', target.host + ':' + target.port]);
  maxApi.outlet(['last', lastSent]);
});

// notein left=note, middle=velocity → patcher packs them as
// [note, velocity] before prepending "note"
maxApi.addHandler('note', (note, velocity) => {
  const n = Number(note) | 0;
  const v = (Number(velocity) | 0) / 127.0;
  if (v <= 0) {
    send('/note/off', n, 0.0);
  } else {
    send('/note/on', n, v);
    lastNote = n;
    send('/note/last', n);
  }
});

// ctlin left=value, middle=cc# → patcher packs them as [value, cc]
// before prepending "cc"
maxApi.addHandler('cc', (value, cc) => {
  const n = Number(cc) | 0;
  const v = (Number(value) | 0) / 127.0;
  send('/cc/' + n, v);
});

maxApi.addHandler('bend', (raw) => {
  // bendin emits 0..16383, centred at 8192. Map to -1..+1.
  let r = Number(raw) | 0;
  // Some devices emit -8192..8191 directly; handle both.
  if (r > 8191) r -= 8192;
  const v = Math.max(-1.0, Math.min(1.0, r / 8192.0));
  send('/pitchbend', v);
});

maxApi.addHandler('aftertouch', (value) => {
  const v = (Number(value) | 0) / 127.0;
  send('/aftertouch', v);
});

maxApi.post('midi_to_osc.js ready, target ' + target.host + ':' + target.port);
maxApi.outlet(['target', target.host + ':' + target.port]);
maxApi.outlet(['last', lastSent]);
