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
const initProc = () => {
    // console.trace("init proc");
    if (proc == null) {
        proc = exec(`conda activate pdm && python "${__dirname}/../main.py" && conda deactivate`, ['pipe', 'pipe', 'pipe']);
        // proc = spawn(pcmd, [__dirname + '/../main.py'], ['pipe', 'pipe', 'pipe']);
        console.log("**************** Created python process | PID: " + proc.pid + " ********************");

        // function myFunc() {
        //     console.log("=======================================================");
        //     console.log("In timeout...");
        //     if (proc) {
        //         console.log(`proc is not null | PID: ${proc.pid}`);
        //         // console.log(proc);
        //         // console.log(`proc.connected = ${proc.connected}`);
        //     } else {
        //         console.log(`proc is null`);
        //     }
        //     console.log("=======================================================");
        //     setTimeout(myFunc, 10000);
        // }
        // myFunc();

        //handle results
        proc.stdout.on('data', (data) => {

            console.log("Outgoing data: " + data.toString());

            // for all nodes (sometimes, due to threading in python, multiple nodeids come seperated by '\n')
            data.toString().trim().split('\n').forEach((_data) => {

                try {
                    // for end node
                    _data = JSON.parse(_data.trim());
                    nodeid = _data.nodeid;
                    node = nodes[nodeid];
                    if (_data.msg == 'error') {
                        node.status(status.NONE);
                    } else {
                        msg = {
                            payload: _data.msg
                        }; // end node will have only one output
                        node.status(status.DONE);
                        node.send(msg);
                    }
                } catch {
                    nodeid = _data.trim();
                    // nodeid = data.toString().trim();
                    node = nodes[nodeid];
                    node.status(status.DONE);

                    // Send all outputs except for the error one (last one, if exists)
                    msg = Array(node.wires.length);
                    for (var i = 0; i < node.wires.length; ++i) {
                        // This data is coming from this output of this node
                        // Read the data coming from there in python
                        msg[i] = {
                            nodeid: node.id,
                            out: i,
                            error: false,
                            payload: node.config.pyfunc + " done!"
                        };
                    }
                    if (node.haserror)
                        msg[node.wires.length - 1] = null;

                    console.log("Data about to be sent:");
                    msg.forEach((m) => {
                        console.log(m);
                    });
                    node.send(msg);
                }
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
                // data.pyfunc = 'load_dataset';
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

                node.send(msg)
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

        // // handle crashes
        // ['beforeExit', 'exit'].forEach((eventType) => {
        //     console.log("Main process listening on " + eventType + " PID: " + proc.pid);
        //     proc.on(eventType, (e, s) => {
        //         if (this)
        //             console.log("Main process recieved " + eventType + " PID: " + this.pid);
        //         else
        //             console.log("Main process recieved " + eventType);
        //         console.trace("In " + eventType);
        //         console.log("e:");
        //         console.log(e);
        //         console.log("s:");
        //         console.log(s);
        //         if (this) {
        //             console.log("connected:");
        //             console.log(this.connected);
        //         }
        //         console.log("e.stack:");
        //         console.log(e.stack);
        //         if (this)
        //             console.log("**************** Exiting main process | PID: " + this.pid + " ********************");
        //         else
        //             console.log("**************** Exiting main process ********************");
        //         proc = null;
        //     });
        // });

        // //catches ctrl+c event
        // ['SIGINT', 'SIGUSR1', 'SIGUSR2', 'SIGTERM', 'close', 'error', 'disconnect'].forEach((eventType) => {
        //     console.log("Main process listening on " + eventType + " PID: " + proc.pid);
        //     proc.on(eventType, () => {
        //         if (this) {
        //             console.log("Main process recieved " + eventType + " PID: " + this.pid);
        //             console.log("connected:");
        //             console.log(this.connected);
        //         } else
        //             console.log("Main process recieved " + eventType);
        //         // if (proc)
        //         //     proc.exit(2);
        //         // proc = null;
        //     });
        // });

        // //catches uncaught exceptions
        // ['uncaughtException', 'unhandledRejection'].forEach((eventType) => {
        //     console.log("Main process listening on " + eventType + " PID: " + proc.pid);
        //     proc.on(eventType, (e) => {
        //         if (this)
        //             console.log("Main process recieved " + eventType + " PID: " + this.pid);
        //         else
        //             console.log("Main process recieved " + eventType);
        //         console.log(e.stack);
        //         // if (proc)
        //         //     proc.exit(99);
        //         // proc = null;
        //     });
        // });

    }
};

//send config as json to python process
const python = (node) => {
    initProc();
    console.log("node:");
    console.log(node);
    proc.stdin.write(JSON.stringify(node.config) + '\n');
};

module.exports = {
    //initialize node
    run: (RED, node, config) => {
        RED.nodes.createNode(node, config);
        node.status(status.NONE);

        initProc();

        console.log("Saving node with id:");
        console.log("    " + node.id);
        nodes[node.id] = node;
        if (node.config.end == undefined) {
            node.config.end = false;
        }

        //handle input
        node.on('input', (msg) => {
            console.log("Input msg:");
            console.log(msg);

            if (msg.error) { // prev node error
                node.status(status.NONE);
                node.config.error = true;
            } else {
                node.status(status.PROCESSING);
                node.config.error = false;
            }

            node.config.topic = node.topic;
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
            // TODO: Tell python to remove this node from the "nodes dict"
            console.log("Called close for node " + node.id);
            node.status(status.NONE);
            delete nodes[node.id];
            if (proc != null) {
                proc.stdin.write('\n'); // this gives python process an exception so that it will terminate
                proc = null;
            }
            done();
        });
    }
};