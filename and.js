[
    {
        "id": "720a0306.478bcc",
        "label": "Flow 2",
        "type": "tab"
    },
    {
        "crontab": "",
        "id": "39557f2d.f1bf3",
        "name": "",
        "once": false,
        "payload": "0",
        "payloadType": "num",
        "repeat": "",
        "topic": "tempsensor",
        "type": "inject",
        "wires": [
            [
                "960c060d.ed70c8",
                "dcfb18f5.719218"
            ]
        ],
        "x": 250,
        "y": 160,
        "z": "720a0306.478bcc"
    },
    {
        "crontab": "",
        "id": "6e3a1969.a0aeb8",
        "name": "",
        "once": false,
        "payload": "0",
        "payloadType": "num",
        "repeat": "",
        "topic": "heattime",
        "type": "inject",
        "wires": [
            [
                "960c060d.ed70c8",
                "dcfb18f5.719218"
            ]
        ],
        "x": 250,
        "y": 411,
        "z": "720a0306.478bcc"
    },
    {
        "crontab": "",
        "id": "e0e9e65f.e6c2c8",
        "name": "",
        "once": false,
        "payload": "1",
        "payloadType": "num",
        "repeat": "",
        "topic": "heattime",
        "type": "inject",
        "wires": [
            [
                "960c060d.ed70c8",
                "dcfb18f5.719218"
            ]
        ],
        "x": 249,
        "y": 360,
        "z": "720a0306.478bcc"
    },
    {
        "crontab": "",
        "id": "87a51d3e.9c2e4",
        "name": "",
        "once": false,
        "payload": "1",
        "payloadType": "num",
        "repeat": "",
        "topic": "tempsensor",
        "type": "inject",
        "wires": [
            [
                "960c060d.ed70c8",
                "dcfb18f5.719218"
            ]
        ],
        "x": 250,
        "y": 200,
        "z": "720a0306.478bcc"
    },
    {
        "active": true,
        "complete": "false",
        "console": "false",
        "id": "28479514.38189a",
        "name": "",
        "type": "debug",
        "wires": [],
        "x": 1150,
        "y": 300,
        "z": "720a0306.478bcc"
    },
    {
        "emitOnlyIfTrue": true,
        "gateType": "and",
        "id": "960c060d.ed70c8",
        "name": "",
        "outputTopic": "",
        "rules": [
            {
                "property": "payload",
                "propertyType": "msg",
                "t": "eq",
                "topic": "tempsensor",
                "v": "1",
                "vt": "num"
            },
            {
                "property": "payload",
                "propertyType": "msg",
                "t": "eq",
                "topic": "heattime",
                "v": "1",
                "vt": "num"
            }
        ],
        "type": "and-gate",
        "wires": [
            [
                "fdfcaf6.6efb55"
            ]
        ],
        "x": 540,
        "y": 300,
        "z": "720a0306.478bcc"
    },
    {
        "emitOnlyIfTrue": true,
        "gateType": "and",
        "id": "dcfb18f5.719218",
        "name": "",
        "outputTopic": "",
        "rules": [
            {
                "property": "payload",
                "propertyType": "msg",
                "t": "eq",
                "topic": "tempsensor",
                "v": "0",
                "vt": "num"
            },
            {
                "property": "payload",
                "propertyType": "msg",
                "t": "eq",
                "topic": "heattime",
                "v": "0",
                "vt": "num"
            }
        ],
        "type": "and-gate",
        "wires": [
            [
                "66e23b59.f35ba4"
            ]
        ],
        "x": 540,
        "y": 200,
        "z": "720a0306.478bcc"
    },
    {
        "action": "",
        "from": "",
        "id": "66e23b59.f35ba4",
        "name": "",
        "property": "",
        "reg": false,
        "rules": [
            {
                "p": "payload",
                "pt": "msg",
                "t": "set",
                "to": "0",
                "tot": "num"
            }
        ],
        "to": "",
        "type": "change",
        "wires": [
            [
                "fdfcaf6.6efb55"
            ]
        ],
        "x": 740,
        "y": 200,
        "z": "720a0306.478bcc"
    },
    {
        "drop": true,
        "id": "fdfcaf6.6efb55",
        "name": "",
        "nbRateUnits": "5",
        "pauseType": "rate",
        "randomFirst": "1",
        "randomLast": "5",
        "randomUnits": "seconds",
        "rate": "1",
        "rateUnits": "minute",
        "timeout": "5",
        "timeoutUnits": "seconds",
        "type": "delay",
        "wires": [
            [
                "28479514.38189a"
            ]
        ],
        "x": 960,
        "y": 300,
        "z": "720a0306.478bcc"
    }
]
