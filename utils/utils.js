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
        // proc = spawn(pcmd, [__dirname + '/../main.py'], ['pipe', 'pipe', 'pipe']);
        console.log("**************** Created python process | PID: " + proc.pid + " ********************");

        //handle results
        proc.stdout.on('data', (data) => {

            console.log("Outgoing data: " + data.toString());

            // for all nodes (sometimes, due to threading in python, multiple inputs come seperated by '\n')
            data.toString().trim().split('\n').forEach((_data) => {

                _data = JSON.parse(_data.trim());
                nodeid = _data.nodeid;
                node = nodes[nodeid];
                if (_data.status) {
                    node.status(status.TEXT(_data.status));
                    return;
                } else if (_data.msg) {
                    if (_data.msg == 'error') { // Previous node had an error
                        node.status(status.NONE);
                        return;
                    } else {
                        msg = {
                            payload: _data.msg
                        }; // end node will have only one output
                        // TODO: Give this node the ability to have multiple outputs
                    }
                } else {
                    msg = Array(node.wires.length);
                    for (var i = 0; i < node.wires.length; ++i) {
                        // This data is coming from this output of this node
                        // Read the data coming from there in python
                        msg[i] = {
                            nodeid: node.id,
                            out: i,
                            error: false,
                            payload: node.config.pynode + " done!"
                        };
                    }
                    console.log("Data about to be sent:");
                    msg.forEach((m) => {
                        console.log(m);
                    });
                }
                if (_data.cont == undefined)
                    node.status(status.DONE);
                else
                    node.status(status.COUNT(_data.cont));
                node.send(msg);
            });
        });

        //handle errors
        proc.stderr.on('data', (data) => {

            console.log("\n\nNode error:");
            console.log("============================")
            try {
                console.log("stderr in try");
                console.log(JSON.parse(data.toString()).error);
            } catch (err) {
                console.log("stderr in catch");
                console.log(data.toString());
            }
            console.log("============================")
            console.log("\n\n");

            try {
                data = JSON.parse(data.toString());
                // data = {}
                // data.pynode = 'load_dataset';
                // data.error = 'error';
                node = nodes[data.nodeid];
                node.status(status.ERROR)

                msg = Array.from(Array(node.wires.length), (x, i) =>
                    error = {
                        nodeid: node.id,
                        out: i,
                        payload: data.error,
                        error: true
                    }
                );

                node.send(msg);
                // node.error(msg);
            } catch (err) {
                console.log("In stderr of process | Catched error:");
                console.log("err: " + err);
                console.log(data.toString());
            }
        });

        proc.on('exit', () => {
            if (proc)
                console.log(`**************** Process terminated ****************`);
            else
                console.log(`**************** Process terminated | PID: ${proc.pid} ****************`);
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