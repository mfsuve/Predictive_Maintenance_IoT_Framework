module.exports = function(RED) {
    function CombineDataNode(config) {

        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'Combine';

        node.config = {
            numData: parseInt(config.numData)
        };

        utils.run(RED, node, config);
    }
    RED.nodes.registerType('combine data', CombineDataNode);
}