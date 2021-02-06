/**
 * I took this code from this repository:
 * https://github.com/GabrieleMaurina/node-red-contrib-machine-learning
 * and I expanded on it.
 */

const status = require('./status.js');
const { spawn } = require('child_process');
// var fs = require('fs');

var proc = null;
var nodes = {};

// initialize child process
const initProc = (env) => {
    if (proc == null) {
        proc = spawn(`conda activate ${env} && python "${__dirname}/../main.py"`, {
            stdio: 'pipe',
            shell: true
        });
        console.log("**************** Created python process ********************");

        //handle results
        proc.stdout.on('data', (data) => {

            console.log("===============");
            console.log("Outgoing data: " + data.toString());
            console.log("===============");

            // for all nodes (sometimes, due to threading in python, multiple inputs come seperated by '\n')
            data.toString().trim().split('\n').forEach((_data) => {

                console.log("Splitted data:");
                console.log("===============");
                console.log(_data);
                console.log("===============");

                _data = JSON.parse(_data.trim());
                nodeid = _data.nodeid;
                node = nodes[nodeid];

                if (_data.status) {
                    // Change Status Text
                    node.status(node.currentStatus.text(_data.status).get());
                } else if (_data.done) {
                    // Set status as 'DONE'
                    node.status(node.currentStatus.fill('green').get());
                } else if (_data.processing) {
                    // Set status as 'PROCESSING'
                    node.status(node.currentStatus.fill('yellow').get());
                } else if (_data.none) {
                    // Set status as 'NONE' (clear status)
                    node.status(node.currentStatus.clear());
                } else if (_data.warning) {
                    // Display warning message
                    node.warn(_data.warning);
                    node.status(node.currentStatus.fill('blue').get());
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
                    node.send(message);
                }
            });
        });

        // handle errors
        proc.stderr.on('data', (data) => {

            // for all nodes (sometimes, due to threading in python, multiple inputs come seperated by '\n')
            data.toString().trim().split('\n').forEach((_data) => {

                console.log("\n\nNode error:");
                console.log("============================");
                try {
                    console.log("stderr in try");
                    console.log(JSON.parse(_data.toString()).error);
                    console.log("============================");
                    console.log(JSON.parse(_data.toString()));
                } catch (err) {
                    console.log("stderr in catch");
                    console.log("Error is:\n", err);
                    console.log(_data.toString());
                }
                console.log("============================");
                console.log("\n\n");

                try {
                    _data = JSON.parse(_data.toString());
                    node = nodes[_data.nodeid];
                    node.status(node.currentStatus.fill('red').text('error').get())
                    node.error(_data.error);
                } catch (err) {
                    console.log("In stderr of process | Catched error:");
                    console.log("err: " + err);
                    console.log(_data.toString());
                }
            });
        });
    }
};

// send config as json to python process
const python = (config) => {
    // console.log("config:");
    // console.log(config);
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
        node.currentStatus = new status.Status();

        console.log("Saving node with id:");
        console.log("    " + node.id);
        nodes[node.id] = node;

        // console.log(node);
        // Node creationon python
        python({
            id: node.id,
            pynode: node.pynode,
            wires: node.wires,
            config: node.config,
            create: true
        });

        // handle input
        node.on('input', (msg) => {
            // console.log("Input msg:");
            // console.log(msg);

            if (node.onmessage != undefined)
                node.onmessage(msg);

            node.config.id = node.id;

            // Send the actual message to the node as well
            node.config.msg = msg.payload;

            // Send to python process
            // console.log("node:");
            // console.log(node);
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