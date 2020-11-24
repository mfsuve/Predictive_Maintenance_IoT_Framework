module.exports = function(RED) {
    function TestModelNode(config) {

        const utils = require('../../utils/utils');

        var node = this;

        node.topic = 'Test';
        // Corresponding python class
        node.pynode = 'TestModel';

        node.hideProcessing = true;

        node.config = {
            accuracy: config.accuracy,
            precision: config.precision,
            recall: config.recall,
            f1: config.f1,
            resetAfterTraining: config.resetAfterTraining
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("test model", TestModelNode);
}