module.exports = function(RED) {
    function TrainTestSplitNode(config) {

        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'Split';

        node.config = {
            testPercentage: parseInt(config.testPercentage)
        };

        utils.run(RED, node, config);
    }
    RED.nodes.registerType('train test split', TrainTestSplitNode);
}