module.exports = function(RED) {
    function EncoderNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';

        node.config = {
            // Corresponding python class
            pynode: 'Encoder',
            encode: config.encode,
            // persist: config.persist
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("encoder", EncoderNode);
}