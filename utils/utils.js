/**
 * I took this code from this repository:
 * https://github.com/GabrieleMaurina/node-red-contrib-machine-learning
 * and I expanded on it.
 */

const status = require('./status.js')
const { exec } = require('child_process')

var proc = null;
var nodes = {};

//initialize child process
// TODO: her node için ayrı bir process aç
// TODO: ** Bunu python'da açmam lazım, çünkü nodered üzerinden python'daki data paylaşımını yapamıyorum
const initProc = (env) => {
    // console.trace("init proc");
    if (proc == null) {
        proc = exec(`conda activate ${env} && python "${__dirname}/../main.py" && conda deactivate`, ['pipe', 'pipe', 'pipe']);
        console.log("**************** Created python process ********************");

        //handle results
        proc.stdout.on('data', (data) => {

            // console.log("Outgoing data: " + data.toString());

            // for all nodes (sometimes, due to threading in python, multiple inputs come seperated by '\n')
            data.toString().trim().split('\n').forEach((_data) => {

                _data = JSON.parse(_data.trim());
                nodeid = _data.nodeid;
                node = nodes[nodeid];

                if (_data.status) {
                    // Change Status
                    node.status(status.TEXT(_data.status));
                } else if (_data.done) {
                    // Set status as 'DONE'
                    node.status(status.DONE);
                } else if (_data.none) {
                    // Set status as 'NONE' (clear status)
                    node.status(status.NONE);
                } else {
                    // Send message to nodered to print it in debug node
                    message = Array(node.wires.length);
                    for (var i = 0; i < node.wires.length; ++i) {
                        if (_data.message[i] === null)
                            message[i] = null;
                        else
                            message[i] = {
                                topic: node.topic,
                                payload: _data.message[i]
                            };
                    }
                    console.log("Data about to be sent:");
                    message.forEach((m) => {
                        console.log(m);
                    });
                    // console.log('**************************************************************');
                    // console.log('Node: ' + node.config.pynode);
                    // console.log('node.hideProcessing: ' + node.hideProcessing);
                    // console.log('!node.hideProcessing: ' + !node.hideProcessing);
                    // console.log('**************************************************************');
                    // if (!node.hideProcessing)
                    //     node.status(status.PROCESSING);
                    node.send(message);
                }
            });
        });

        //handle errors
        proc.stderr.on('data', (data) => {

            console.log("\n\nNode error:");
            console.log("============================");
            try {
                console.log("stderr in try");
                console.log(JSON.parse(data.toString()).error);
                console.log("============================");
                console.log(JSON.parse(data.toString()));
            } catch (err) {
                console.log("stderr in catch");
                console.log(data.toString());
            }
            console.log("============================");
            console.log("\n\n");

            try {
                data = JSON.parse(data.toString());
                node = nodes[data.nodeid];
                node.status(status.ERROR)
                node.error(data.error);
            } catch (err) {
                console.log("In stderr of process | Catched error:");
                console.log("err: " + err);
                console.log(data.toString());
            }
        });
    }
};

//send config as json to python process
const python = (config) => {
    // initProc('pdm');
    console.log("*********************** proc.stdin.destroyed: " + proc.stdin.destroyed);
    console.log("*********************** proc.stdin.writable: " + proc.stdin.writable);
    proc.stdin.write(JSON.stringify(config) + '\n');
};

module.exports = {
    //initialize node
    run: (RED, node, config) => {
        RED.nodes.createNode(node, config);
        node.status(status.NONE);

        initProc('pdm');

        if (node.config === undefined)
            node.config = {};

        console.log("Saving node with id:");
        console.log("    " + node.id);
        nodes[node.id] = node;

        console.log(node);
        // Node creationon python
        python({
            id: node.id,
            pynode: node.pynode,
            wires: node.wires,
            config: node.config,
            create: true
        });

        //handle input
        node.on('input', (msg) => {
            console.log("Input msg:");
            console.log(msg);

            if (node.onmessage != undefined)
                node.onmessage(msg);

            if (!node.hideProcessing)
                node.status(status.PROCESSING);

            node.config.id = node.id;

            // Send the actual message to the node as well
            node.config.msg = msg.payload;

            // send to python process
            console.log("node:");
            console.log(node);
            python(node.config);
        });

        node.on('close', (done) => {
            console.log("Called close for node " + node.id);
            node.status(status.NONE);
            delete nodes[node.id];
            if (proc != null) {
                proc.stdin.write('\n'); // this gives python process a json exception so that it will terminate
                proc = null;
            }
            done();
        });
    }
};