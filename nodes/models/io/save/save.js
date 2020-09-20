module.exports = function(RED) {
    function SaveNode(config) {

        // const path = require('path');
        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'model';
        // Corresponding python class
        node.pynode = 'SaveModel';

        node.config = {
            folder: config.foldername.trim(),
            prefix: config.prefix.trim()
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("save", SaveNode);
}