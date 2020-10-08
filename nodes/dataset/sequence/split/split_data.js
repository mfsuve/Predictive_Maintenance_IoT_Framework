module.exports = function(RED) {
    function SplitDataNode(config) {

        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'Split';

        node.config = {
            splitPercentage: parseInt(config.splitPercentage),
            shuffle: config.shuffle
        };

        utils.run(RED, node, config);
    }
    RED.nodes.registerType('split data', SplitDataNode);
}