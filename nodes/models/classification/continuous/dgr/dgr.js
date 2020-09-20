module.exports = function(RED) {
    function DGRNode(config) {

        const path = require('path');
        const utils = require('../../../../../utils/utils');

        var node = this;

        node.topic = 'DGR'; // TODO: topic'leri düzenle
        // Corresponding python class
        node.pynode = 'DeepGenerativeReplay';

        node.hideProcessing = true;

        node.config = {
            // * Classifier Parameters
            CLayers: parseInt(config.CLayers),
            CHidden: parseInt(config.CHidden),
            CHiddenSmooth: Boolean(config.CHasSmooth) ? parseInt(config.CHiddenSmooth) : undefined,
            Clr: parseFloat(config.Clr),
            // * Training and Data Parameters
            taskSize: Math.max(10, parseInt(config.taskSize)),
            epochs: Math.max(1, parseInt(config.epochs)),
            batchSize: Math.max(1, parseInt(config.batchSize)),
        };

        // * Generator Parameters
        if (Boolean(config.autoGenParams)) {
            node.config.GZdim = 0;
            node.config.GLayers = node.config.CLayers;
            node.config.GHidden = node.config.CHidden;
            node.config.GHiddenSmooth = node.config.CHiddenSmooth;
            node.config.Glr = node.config.Clr;
        } else {
            node.config.GZdim = parseInt(config.GZdim);
            node.config.GLayers = parseInt(config.GLayers);
            node.config.GHidden = parseInt(config.GHidden);
            node.config.GHiddenSmooth = Boolean(config.GHasSmooth) ? parseInt(config.GHiddenSmooth) : undefined;
            node.config.Glr = parseFloat(config.Glr);
        }

        if (config.loadModel)
            node.config.loadFrom = config.loadFolder.trim();

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("dgr", DGRNode);
}