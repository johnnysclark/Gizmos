{
	"patcher" : 	{
		"fileversion" : 1,
		"appversion" : 		{
			"major" : 8,
			"minor" : 5,
			"revision" : 0,
			"architecture" : "x64",
			"modernui" : 1
		}
,
		"classnamespace" : "box",
		"rect" : [ 100.0, 100.0, 760.0, 540.0 ],
		"bglocked" : 0,
		"openinpresentation" : 0,
		"default_fontsize" : 12.0,
		"default_fontface" : 0,
		"default_fontname" : "Arial",
		"gridonopen" : 1,
		"gridsize" : [ 15.0, 15.0 ],
		"gridsnaponopen" : 1,
		"objectsnaponopen" : 1,
		"statusbarvisible" : 2,
		"toolbarvisible" : 1,
		"lefttoolbarpinned" : 0,
		"toptoolbarpinned" : 0,
		"righttoolbarpinned" : 0,
		"bottomtoolbarpinned" : 0,
		"toolbars_unpinned_last_save" : 0,
		"tallnewobj" : 0,
		"boxanimatetime" : 200,
		"enablehscroll" : 1,
		"enablevscroll" : 1,
		"devicewidth" : 0.0,
		"description" : "",
		"digest" : "",
		"tags" : "",
		"style" : "",
		"subpatcher_template" : "",
		"assistshowspatchername" : 0,
		"boxes" : [
			{ "box" : { "id" : "obj-1",  "maxclass" : "comment", "text" : "MidiToOSC — note/CC/bend/aftertouch → OSC over UDP. Edit host/port via the messages below. Wrap as .amxd via 'Edit Patch in Max' inside Live.", "patching_rect" : [ 20.0, 20.0, 700.0, 22.0 ], "numinlets" : 1, "numoutlets" : 0 } },

			{ "box" : { "id" : "obj-midiin",  "maxclass" : "newobj", "text" : "midiin", "patching_rect" : [ 20.0, 60.0, 50.0, 22.0 ], "numinlets" : 1, "numoutlets" : 1, "outlettype" : [ "int" ] } },
			{ "box" : { "id" : "obj-midiout", "maxclass" : "newobj", "text" : "midiout", "patching_rect" : [ 20.0, 100.0, 50.0, 22.0 ], "numinlets" : 1, "numoutlets" : 0 } },

			{ "box" : { "id" : "obj-notein", "maxclass" : "newobj", "text" : "notein", "patching_rect" : [ 100.0, 60.0, 50.0, 22.0 ], "numinlets" : 1, "numoutlets" : 3, "outlettype" : [ "int", "int", "int" ] } },
			{ "box" : { "id" : "obj-packnote", "maxclass" : "newobj", "text" : "pack 0 0", "patching_rect" : [ 100.0, 100.0, 70.0, 22.0 ], "numinlets" : 2, "numoutlets" : 1, "outlettype" : [ "" ] } },
			{ "box" : { "id" : "obj-prepnote", "maxclass" : "newobj", "text" : "prepend note", "patching_rect" : [ 100.0, 140.0, 90.0, 22.0 ], "numinlets" : 1, "numoutlets" : 1, "outlettype" : [ "" ] } },

			{ "box" : { "id" : "obj-ctlin", "maxclass" : "newobj", "text" : "ctlin", "patching_rect" : [ 220.0, 60.0, 40.0, 22.0 ], "numinlets" : 1, "numoutlets" : 3, "outlettype" : [ "int", "int", "int" ] } },
			{ "box" : { "id" : "obj-packcc", "maxclass" : "newobj", "text" : "pack 0 0", "patching_rect" : [ 220.0, 100.0, 70.0, 22.0 ], "numinlets" : 2, "numoutlets" : 1, "outlettype" : [ "" ] } },
			{ "box" : { "id" : "obj-prepcc", "maxclass" : "newobj", "text" : "prepend cc", "patching_rect" : [ 220.0, 140.0, 80.0, 22.0 ], "numinlets" : 1, "numoutlets" : 1, "outlettype" : [ "" ] } },

			{ "box" : { "id" : "obj-bendin", "maxclass" : "newobj", "text" : "bendin", "patching_rect" : [ 340.0, 60.0, 50.0, 22.0 ], "numinlets" : 1, "numoutlets" : 2, "outlettype" : [ "int", "int" ] } },
			{ "box" : { "id" : "obj-prepbend", "maxclass" : "newobj", "text" : "prepend bend", "patching_rect" : [ 340.0, 140.0, 90.0, 22.0 ], "numinlets" : 1, "numoutlets" : 1, "outlettype" : [ "" ] } },

			{ "box" : { "id" : "obj-touchin", "maxclass" : "newobj", "text" : "touchin", "patching_rect" : [ 460.0, 60.0, 60.0, 22.0 ], "numinlets" : 1, "numoutlets" : 2, "outlettype" : [ "int", "int" ] } },
			{ "box" : { "id" : "obj-prepaft", "maxclass" : "newobj", "text" : "prepend aftertouch", "patching_rect" : [ 460.0, 140.0, 130.0, 22.0 ], "numinlets" : 1, "numoutlets" : 1, "outlettype" : [ "" ] } },

			{ "box" : { "id" : "obj-msg-host", "maxclass" : "message", "text" : "host 127.0.0.1", "patching_rect" : [ 20.0, 200.0, 110.0, 22.0 ], "numinlets" : 2, "numoutlets" : 1, "outlettype" : [ "" ] } },
			{ "box" : { "id" : "obj-msg-port", "maxclass" : "message", "text" : "port 7000", "patching_rect" : [ 140.0, 200.0, 80.0, 22.0 ], "numinlets" : 2, "numoutlets" : 1, "outlettype" : [ "" ] } },
			{ "box" : { "id" : "obj-msg-status", "maxclass" : "message", "text" : "status", "patching_rect" : [ 230.0, 200.0, 60.0, 22.0 ], "numinlets" : 2, "numoutlets" : 1, "outlettype" : [ "" ] } },

			{ "box" : { "id" : "obj-node", "maxclass" : "newobj", "text" : "node.script midi_to_osc.js @autostart 1", "patching_rect" : [ 20.0, 260.0, 290.0, 22.0 ], "numinlets" : 1, "numoutlets" : 2, "outlettype" : [ "", "" ] } },

			{ "box" : { "id" : "obj-route", "maxclass" : "newobj", "text" : "route target last error", "patching_rect" : [ 20.0, 320.0, 180.0, 22.0 ], "numinlets" : 1, "numoutlets" : 4, "outlettype" : [ "", "", "", "" ] } },

			{ "box" : { "id" : "obj-disp-target", "maxclass" : "comment", "text" : "target: (waiting)", "patching_rect" : [ 20.0, 360.0, 280.0, 22.0 ], "numinlets" : 1, "numoutlets" : 0 } },
			{ "box" : { "id" : "obj-disp-last",   "maxclass" : "comment", "text" : "last: (none)", "patching_rect" : [ 20.0, 390.0, 480.0, 22.0 ], "numinlets" : 1, "numoutlets" : 0 } },
			{ "box" : { "id" : "obj-disp-err",    "maxclass" : "comment", "text" : "errors: (none)", "patching_rect" : [ 20.0, 420.0, 480.0, 22.0 ], "numinlets" : 1, "numoutlets" : 0 } },

			{ "box" : { "id" : "obj-led", "maxclass" : "led", "patching_rect" : [ 310.0, 360.0, 24.0, 24.0 ], "numinlets" : 1, "numoutlets" : 1, "outlettype" : [ "" ], "bgcolor" : [ 0.2, 0.2, 0.2, 1.0 ], "activebgoncolor" : [ 0.2, 0.9, 0.4, 1.0 ] } },
			{ "box" : { "id" : "obj-led-pulse", "maxclass" : "newobj", "text" : "t 1 0", "patching_rect" : [ 310.0, 330.0, 40.0, 22.0 ], "numinlets" : 1, "numoutlets" : 2, "outlettype" : [ "int", "int" ] } },
			{ "box" : { "id" : "obj-led-delay", "maxclass" : "newobj", "text" : "delay 60", "patching_rect" : [ 350.0, 330.0, 60.0, 22.0 ], "numinlets" : 2, "numoutlets" : 1, "outlettype" : [ "bang" ] } },

			{ "box" : { "id" : "obj-print", "maxclass" : "newobj", "text" : "print osc", "patching_rect" : [ 220.0, 260.0, 70.0, 22.0 ], "numinlets" : 1, "numoutlets" : 0 } }
		],
		"lines" : [
			{ "patchline" : { "source" : [ "obj-midiin", 0 ],     "destination" : [ "obj-midiout", 0 ] } },

			{ "patchline" : { "source" : [ "obj-notein", 0 ],     "destination" : [ "obj-packnote", 0 ] } },
			{ "patchline" : { "source" : [ "obj-notein", 1 ],     "destination" : [ "obj-packnote", 1 ] } },
			{ "patchline" : { "source" : [ "obj-packnote", 0 ],   "destination" : [ "obj-prepnote", 0 ] } },
			{ "patchline" : { "source" : [ "obj-prepnote", 0 ],   "destination" : [ "obj-node", 0 ] } },

			{ "patchline" : { "source" : [ "obj-ctlin", 0 ],      "destination" : [ "obj-packcc", 0 ] } },
			{ "patchline" : { "source" : [ "obj-ctlin", 1 ],      "destination" : [ "obj-packcc", 1 ] } },
			{ "patchline" : { "source" : [ "obj-packcc", 0 ],     "destination" : [ "obj-prepcc", 0 ] } },
			{ "patchline" : { "source" : [ "obj-prepcc", 0 ],     "destination" : [ "obj-node", 0 ] } },

			{ "patchline" : { "source" : [ "obj-bendin", 0 ],     "destination" : [ "obj-prepbend", 0 ] } },
			{ "patchline" : { "source" : [ "obj-prepbend", 0 ],   "destination" : [ "obj-node", 0 ] } },

			{ "patchline" : { "source" : [ "obj-touchin", 0 ],    "destination" : [ "obj-prepaft", 0 ] } },
			{ "patchline" : { "source" : [ "obj-prepaft", 0 ],    "destination" : [ "obj-node", 0 ] } },

			{ "patchline" : { "source" : [ "obj-msg-host", 0 ],   "destination" : [ "obj-node", 0 ] } },
			{ "patchline" : { "source" : [ "obj-msg-port", 0 ],   "destination" : [ "obj-node", 0 ] } },
			{ "patchline" : { "source" : [ "obj-msg-status", 0 ], "destination" : [ "obj-node", 0 ] } },

			{ "patchline" : { "source" : [ "obj-node", 0 ],       "destination" : [ "obj-print", 0 ] } },
			{ "patchline" : { "source" : [ "obj-node", 0 ],       "destination" : [ "obj-route", 0 ] } },

			{ "patchline" : { "source" : [ "obj-route", 0 ],      "destination" : [ "obj-disp-target", 0 ] } },
			{ "patchline" : { "source" : [ "obj-route", 1 ],      "destination" : [ "obj-disp-last", 0 ] } },
			{ "patchline" : { "source" : [ "obj-route", 1 ],      "destination" : [ "obj-led-pulse", 0 ] } },
			{ "patchline" : { "source" : [ "obj-route", 2 ],      "destination" : [ "obj-disp-err", 0 ] } },

			{ "patchline" : { "source" : [ "obj-led-pulse", 0 ],  "destination" : [ "obj-led", 0 ] } },
			{ "patchline" : { "source" : [ "obj-led-pulse", 1 ],  "destination" : [ "obj-led-delay", 0 ] } },
			{ "patchline" : { "source" : [ "obj-led-delay", 0 ],  "destination" : [ "obj-led", 0 ] } }
		]
	}
}
