module.exports = function(RED) {
    function TrainTestSplitNode(config) {

        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';

        node.config = {
            // Corresponding python class
            pynode: 'Split',
            testPercentage: config.testPercentage
        };

        utils.run(RED, node, config);
    }
    RED.nodes.registerType('train test split', TrainTestSplitNode);
}