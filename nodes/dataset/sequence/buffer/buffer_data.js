module.exports = function(RED) {
    function BufferDataNode(config) {

        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'Buffer';

        node.config = {
            maxData: parseInt(config.maxData)
        };

        utils.run(RED, node, config);
    }
    RED.nodes.registerType('buffer data', BufferDataNode);
}