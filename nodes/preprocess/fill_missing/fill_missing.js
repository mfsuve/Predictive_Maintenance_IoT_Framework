module.exports = function(RED) {
    function FillMissingNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'FillMissing';

        node.config = {
            preFillConstant: parseFloat(config.preFillConstant) || 0,
            preFillSelect: config.preFillSelect,
            postFillConstant: parseFloat(config.postFillConstant) || 0,
            postFillSelect: config.postFillSelect
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("fill missing", FillMissingNode);
}