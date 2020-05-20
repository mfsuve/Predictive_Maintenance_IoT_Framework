module.exports = function(RED) {
    function TestModelNode(config) {

        const path = require('path');
        const utils = require('../../utils/utils');

        var node = this;

        node.topic = 'test';

        node.config = {
            // Corresponding python class
            pynode: 'TestModel',
            metric: config.metric
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("test model", TestModelNode);
}