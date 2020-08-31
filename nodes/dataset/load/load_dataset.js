module.exports = function(RED) {
    function LoadDatasetNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';

        node.config = {
            // Corresponding python class
            pynode: 'LoadDataset',
            configPath: config.configPath,
            isFile: config.method == 'file',
            col: parseInt(config.col),
            hasheader: config.hasheader,
            removeAllnan: config.removeAllnan,
            removeAllsame: config.removeAllsame,
            hasTarget: config.hasTarget,
        };
        node.onmessage = (msg) => {
            if (node.config.isFile) {
                if (config.payloadFilename)
                    node.config.path = path.join(config.foldername.trim(), msg.payload.trim());
                else
                    node.config.path = path.join(config.foldername.trim(), config.filename.trim());
            } else
                node.config.path = '';
        }

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("load dataset", LoadDatasetNode);
}