module.exports = function(RED) {
    function EncoderNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'Encoder';

        node.config = {
            encode: config.encode,
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("encoder", EncoderNode);
}