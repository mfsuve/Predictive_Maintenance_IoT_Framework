module.exports = function(RED) {
    function TestModelNode(config) {

        const utils = require('../../utils/utils');

        var node = this;

        node.topic = 'Test';

        node.config = {
            // Corresponding python class
            pynode: 'TestModel',
            accuracy: config.accuracy,
            precision: config.precision,
            recall: config.recall,
            f1: config.f1
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("test model", TestModelNode);
}