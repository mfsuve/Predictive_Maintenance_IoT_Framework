module.exports = function(RED) {
    function StoreDataNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'StoreDataset';

        node.config = {
            numrows: parseInt(config.numrows),
            path: path.join(config.foldername.trim(), config.filename.trim())
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("store data", StoreDataNode);
}