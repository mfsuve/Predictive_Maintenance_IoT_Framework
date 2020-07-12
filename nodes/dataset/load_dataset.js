module.exports = function(RED) {
    function LoadDatasetNode(config) {

        const path = require('path');
        const utils = require('../../utils/utils');

        var node = this;

        node.topic = 'data';

        node.config = {
            // Corresponding python class
            pynode: 'LoadDataset',
            // path: path.join(config.foldername, config.filename),
            col: parseInt(config.col),
            hasheader: Boolean(config.hasheader),
            encode: config.encode,
            fillConstant: config.fillConstant,
            fillSelect: config.fillSelect,
            removeAllnan: config.removeAllnan,
            removeAllsame: config.removeAllsame,
            onlyTest: config.onlyTest
        };
        node.onmessage = (msg) => {
            if (config.payloadFilename)
                node.config.path = path.join(config.foldername, msg.payload);
            else
                node.config.path = path.join(config.foldername, config.filename);
        }

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("load dataset", LoadDatasetNode);
}