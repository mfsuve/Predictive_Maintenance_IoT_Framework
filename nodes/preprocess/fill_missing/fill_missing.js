module.exports = function(RED) {
    function FillMissingNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'FillMissing';

        node.config = {
            fillConstant: config.fillConstant,
            fillSelect: config.fillSelect,
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("fill missing", FillMissingNode);
}