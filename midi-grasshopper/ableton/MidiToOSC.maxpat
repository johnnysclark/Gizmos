{
	"patcher": {
		"fileversion": 1,
		"appversion": {
			"major": 8,
			"minor": 6,
			"revision": 0,
			"architecture": "x64",
			"modernui": 1
		},
		"classnamespace": "box",
		"rect": [40.0, 100.0, 760.0, 560.0],
		"bglocked": 0,
		"openinpresentation": 1,
		"default_fontsize": 12.0,
		"default_fontface": 0,
		"default_fontname": "Arial",
		"gridonopen": 1,
		"gridsize": [15.0, 15.0],
		"gridsnaponopen": 1,
		"objectsnaponopen": 1,
		"statusbarvisible": 2,
		"toolbarvisible": 1,
		"lefttoolbarpinned": 0,
		"toptoolbarpinned": 0,
		"righttoolbarpinned": 0,
		"bottomtoolbarpinned": 0,
		"toolbars_unpinned_last_save": 0,
		"tallnewobj": 0,
		"boxanimatetime": 200,
		"enablehscroll": 1,
		"enablevscroll": 1,
		"devicewidth": 480.0,
		"description": "",
		"digest": "",
		"tags": "",
		"style": "",
		"subpatcher_template": "",
		"assistshowspatchername": 0,
		"boxes": [
			{
				"box": {
					"id": "obj-thisdevice",
					"maxclass": "live.thisdevice",
					"numinlets": 1,
					"numoutlets": 3,
					"outlettype": ["bang", "bang", ""],
					"patching_rect": [20.0, 20.0, 80.0, 22.0]
				}
			},
			{
				"box": {
					"id": "obj-header",
					"maxclass": "comment",
					"numinlets": 1,
					"numoutlets": 0,
					"patching_rect": [120.0, 20.0, 480.0, 22.0],
					"text": "MIDI → OSC bridge. Default target: 127.0.0.1:7000"
				}
			},

			{
				"box": {
					"id": "obj-notein",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 3,
					"outlettype": ["int", "int", "int"],
					"patching_rect": [20.0, 70.0, 60.0, 22.0],
					"text": "notein"
				}
			},
			{
				"box": {
					"id": "obj-prepend-note",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [20.0, 110.0, 90.0, 22.0],
					"text": "prepend /note"
				}
			},
			{
				"box": {
					"id": "obj-prepend-vel",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [120.0, 110.0, 110.0, 22.0],
					"text": "prepend /velocity"
				}
			},

			{
				"box": {
					"id": "obj-ctlin",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 3,
					"outlettype": ["int", "int", "int"],
					"patching_rect": [260.0, 70.0, 50.0, 22.0],
					"text": "ctlin"
				}
			},
			{
				"box": {
					"id": "obj-cc-fmt",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [320.0, 110.0, 140.0, 22.0],
					"text": "sprintf set /cc/%ld"
				}
			},
			{
				"box": {
					"id": "obj-prepend-cc",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [260.0, 150.0, 100.0, 22.0],
					"text": "prepend /tmp"
				}
			},

			{
				"box": {
					"id": "obj-bendin",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 2,
					"outlettype": ["int", "int"],
					"patching_rect": [480.0, 70.0, 60.0, 22.0],
					"text": "bendin"
				}
			},
			{
				"box": {
					"id": "obj-prepend-bend",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [480.0, 110.0, 90.0, 22.0],
					"text": "prepend /bend"
				}
			},

			{
				"box": {
					"id": "obj-touchin",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 2,
					"outlettype": ["int", "int"],
					"patching_rect": [600.0, 70.0, 70.0, 22.0],
					"text": "touchin"
				}
			},
			{
				"box": {
					"id": "obj-prepend-touch",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [600.0, 110.0, 140.0, 22.0],
					"text": "prepend /aftertouch"
				}
			},

			{
				"box": {
					"id": "obj-tee",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 2,
					"outlettype": ["", ""],
					"patching_rect": [260.0, 250.0, 50.0, 22.0],
					"text": "t l l"
				}
			},
			{
				"box": {
					"id": "obj-udpsend",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 0,
					"patching_rect": [260.0, 380.0, 200.0, 22.0],
					"text": "udpsend 127.0.0.1 7000"
				}
			},
			{
				"box": {
					"id": "obj-last-msg",
					"maxclass": "message",
					"numinlets": 2,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [480.0, 250.0, 240.0, 22.0],
					"presentation": 1,
					"presentation_rect": [10.0, 110.0, 460.0, 22.0],
					"text": "(no messages yet)"
				}
			},
			{
				"box": {
					"id": "obj-led",
					"maxclass": "live.toggle",
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": ["int"],
					"parameter_enable": 0,
					"patching_rect": [200.0, 250.0, 24.0, 24.0],
					"presentation": 1,
					"presentation_rect": [10.0, 140.0, 24.0, 24.0]
				}
			},
			{
				"box": {
					"id": "obj-led-off",
					"maxclass": "newobj",
					"numinlets": 2,
					"numoutlets": 1,
					"outlettype": ["bang"],
					"patching_rect": [200.0, 290.0, 50.0, 22.0],
					"text": "delay 100"
				}
			},
			{
				"box": {
					"id": "obj-led-zero",
					"maxclass": "message",
					"numinlets": 2,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [200.0, 320.0, 32.0, 22.0],
					"text": "0"
				}
			},

			{
				"box": {
					"id": "obj-host-label",
					"maxclass": "comment",
					"numinlets": 1,
					"numoutlets": 0,
					"patching_rect": [40.0, 200.0, 60.0, 22.0],
					"presentation": 1,
					"presentation_rect": [10.0, 20.0, 60.0, 22.0],
					"text": "host"
				}
			},
			{
				"box": {
					"id": "obj-host",
					"maxclass": "comment",
					"numinlets": 1,
					"numoutlets": 0,
					"patching_rect": [110.0, 200.0, 140.0, 22.0],
					"presentation": 1,
					"presentation_rect": [80.0, 20.0, 200.0, 22.0],
					"text": "127.0.0.1"
				}
			},
			{
				"box": {
					"id": "obj-host-msg",
					"maxclass": "message",
					"numinlets": 2,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [40.0, 230.0, 140.0, 22.0],
					"text": "host 127.0.0.1"
				}
			},

			{
				"box": {
					"id": "obj-port-label",
					"maxclass": "comment",
					"numinlets": 1,
					"numoutlets": 0,
					"patching_rect": [40.0, 350.0, 60.0, 22.0],
					"presentation": 1,
					"presentation_rect": [10.0, 60.0, 60.0, 22.0],
					"text": "port"
				}
			},
			{
				"box": {
					"id": "obj-port",
					"maxclass": "live.numbox",
					"numinlets": 1,
					"numoutlets": 2,
					"outlettype": ["", "float"],
					"parameter_enable": 1,
					"saved_attribute_attributes": {
						"valueof": {
							"parameter_initial": [7000],
							"parameter_initial_enable": 1,
							"parameter_longname": "port",
							"parameter_mmax": 65535,
							"parameter_mmin": 1024,
							"parameter_shortname": "port",
							"parameter_type": 1,
							"parameter_unitstyle": 0
						}
					},
					"patching_rect": [110.0, 350.0, 80.0, 22.0],
					"presentation": 1,
					"presentation_rect": [80.0, 60.0, 80.0, 22.0],
					"varname": "port"
				}
			},
			{
				"box": {
					"id": "obj-port-fmt",
					"maxclass": "newobj",
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"patching_rect": [110.0, 380.0, 90.0, 22.0],
					"text": "prepend port"
				}
			},

			{
				"box": {
					"id": "obj-hint",
					"maxclass": "comment",
					"numinlets": 1,
					"numoutlets": 0,
					"patching_rect": [40.0, 420.0, 700.0, 22.0],
					"presentation": 1,
					"presentation_rect": [10.0, 180.0, 460.0, 60.0],
					"text": "To rename a CC's OSC address, edit the patch in Max: add a `coll` between ctlin's ctl-number outlet and the sprintf box. To change the host, edit the [host 127.0.0.1] message box, click it, and it sends to udpsend."
				}
			}
		],

		"lines": [
			{"patchline": {"source": ["obj-notein", 0], "destination": ["obj-prepend-note", 0]}},
			{"patchline": {"source": ["obj-notein", 1], "destination": ["obj-prepend-vel", 0]}},
			{"patchline": {"source": ["obj-prepend-note", 0], "destination": ["obj-tee", 0]}},
			{"patchline": {"source": ["obj-prepend-vel", 0], "destination": ["obj-tee", 0]}},

			{"patchline": {"source": ["obj-ctlin", 0], "destination": ["obj-prepend-cc", 0]}},
			{"patchline": {"source": ["obj-ctlin", 1], "destination": ["obj-cc-fmt", 0]}},
			{"patchline": {"source": ["obj-cc-fmt", 0], "destination": ["obj-prepend-cc", 0]}},
			{"patchline": {"source": ["obj-prepend-cc", 0], "destination": ["obj-tee", 0]}},

			{"patchline": {"source": ["obj-bendin", 0], "destination": ["obj-prepend-bend", 0]}},
			{"patchline": {"source": ["obj-prepend-bend", 0], "destination": ["obj-tee", 0]}},

			{"patchline": {"source": ["obj-touchin", 0], "destination": ["obj-prepend-touch", 0]}},
			{"patchline": {"source": ["obj-prepend-touch", 0], "destination": ["obj-tee", 0]}},

			{"patchline": {"source": ["obj-tee", 0], "destination": ["obj-udpsend", 0]}},
			{"patchline": {"source": ["obj-tee", 1], "destination": ["obj-last-msg", 0]}},
			{"patchline": {"source": ["obj-tee", 1], "destination": ["obj-led", 0]}},
			{"patchline": {"source": ["obj-led", 0], "destination": ["obj-led-off", 0]}},
			{"patchline": {"source": ["obj-led-off", 0], "destination": ["obj-led-zero", 0]}},
			{"patchline": {"source": ["obj-led-zero", 0], "destination": ["obj-led", 0]}},

			{"patchline": {"source": ["obj-host-msg", 0], "destination": ["obj-udpsend", 0]}},
			{"patchline": {"source": ["obj-port", 0], "destination": ["obj-port-fmt", 0]}},
			{"patchline": {"source": ["obj-port-fmt", 0], "destination": ["obj-udpsend", 0]}}
		]
	}
}
