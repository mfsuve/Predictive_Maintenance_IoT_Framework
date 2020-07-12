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
const initProc = (env) => {
    // console.trace("init proc");
    if (proc == null) {
        proc = exec(`conda activate ${env} && python "${__dirname}/../main.py" && conda deactivate`, ['pipe', 'pipe', 'pipe']);
        console.log("**************** Created python process ********************");

        //handle results
        proc.stdout.on('data', (data) => {

            console.log("Outgoing data: " + data.toString());

            // for all nodes (sometimes, due to threading in python, multiple inputs come seperated by '\n')
            data.toString().trim().split('\n').forEach((_data) => {

                _data = JSON.parse(_data.trim());
                nodeid = _data.nodeid;
                node = nodes[nodeid];

                if (_data.status) {
                    // Change Status
                    node.status(status.TEXT(_data.status));
                    return;
                } else if (_data.prev_error) { // TODO: Buna gerek kalmayabilir, error kısmında node.send yerine node.error dediğimde otomatik kesiyor olabilir
                    // Stop because previous node had an error
                    node.status(status.NONE); // TODO: Try to cascade this message to next nodes
                    return;
                } else if (_data.done) {
                    // Set status as 'DONE'
                    node.status(status.DONE);
                    return;
                } else if (_data.message) {
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
                } else {
                    // Just send a signal to notify the next nodes to continue
                    message = Array(node.wires.length);
                    for (var i = 0; i < node.wires.length; ++i) {
                        message[i] = {
                            nodeid: node.id,
                            out: i,
                            payload: node.config.pynode + " done!"
                        };
                    }
                }
                console.log("Data about to be sent:");
                message.forEach((m) => {
                    console.log(m);
                });
                node.status(status.PROCESSING);
                node.send(message);
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
                // data = {}
                // data.pynode = 'load_dataset';
                // data.error = 'error';
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
const python = (node) => {
    initProc('pdm');
    console.log("node:");
    console.log(node);
    proc.stdin.write(JSON.stringify(node.config) + '\n');
};

module.exports = {
    //initialize node
    run: (RED, node, config) => {
        RED.nodes.createNode(node, config);
        node.status(status.NONE);

        initProc('pdm');

        console.log("Saving node with id:");
        console.log("    " + node.id);
        nodes[node.id] = node;

        //handle input
        node.on('input', (msg) => {
            console.log("Input msg:");
            console.log(msg);

            if (node.onmessage != undefined) {
                node.onmessage(msg);
            }

            if (msg.error) { // prev node error
                node.status(status.NONE);
                node.config.error = true;
            } else {
                node.status(status.PROCESSING);
                node.config.error = false;
            }

            node.config.id = node.id;

            // To be able to get previous node's output
            if (msg.out == undefined) {
                node.config.prevout = -1;
                node.config.prev_nodeid = -1;
            } else {
                node.config.prevout = msg.out;
                node.config.prev_nodeid = msg.nodeid;
            }
            // send to python process
            python(node);
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