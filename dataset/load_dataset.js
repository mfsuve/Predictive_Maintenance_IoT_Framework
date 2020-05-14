module.exports = function(RED) {
    function LoadDatasetNode(config) {

        const path = require('path');
        const utils = require('../utils/utils');

        var node = this;

        node.topic = 'data';
        // Does node have error output
        // node.haserror = true;

        node.config = {
            // Corresponding python function
            pyfunc: 'load_dataset',
            path: path.join(config.foldername, config.filename),
            col: parseInt(config.col),
            hasheader: Boolean(config.hasheader),
            encode: config.encode,
            fillConstant: config.fillConstant,
            fillSelect: config.fillSelect
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("load dataset", LoadDatasetNode);
}