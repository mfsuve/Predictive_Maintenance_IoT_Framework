module.exports = function(RED) {
    function SaveNode(config) {

        // const path = require('path');
        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'model';

        node.config = {
            // Corresponding python class
            pynode: 'SaveModel',
            folder: config.foldername.trim(),
            prefix: config.prefix.trim(),
            timestamp: config.timestamp
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("save", SaveNode);
}