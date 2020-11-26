module.exports = function(RED) {
    function FillMissingNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'FillMissing';

        node.config = {
            // For X
            preFillConstantX: parseFloat(config.preFillConstantX) || 0,
            preFillSelectX: config.preFillSelectX || 'constant',
            postFillConstantX: parseFloat(config.postFillConstantX) || 0,
            postFillSelectX: config.postFillSelectX || 'constant',
            // For Y
            preFillConstantY: parseFloat(config.preFillConstantY) || 0,
            preFillSelectY: config.fillY ? (config.preFillSelectY || 'constant') : 'constant',
            postFillConstantY: parseFloat(config.postFillConstantY) || 0,
            postFillSelectY: config.fillY ? (config.postFillSelectY || 'constant') : 'constant'
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("fill missing", FillMissingNode);
}