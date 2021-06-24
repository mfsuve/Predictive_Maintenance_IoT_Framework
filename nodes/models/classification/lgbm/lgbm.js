module.exports = function(RED) {
    function LightGBMClassifierNode(config) {

        const path = require('path');
        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'LightGBMClassifier';

        node.config = {
            task_size: Math.max(10, parseInt(config.task_size)),
            max_depth: config.unlimited_depth ? -1 : Math.max(1, parseInt(config.max_depth)),
            num_leaves: Math.min(131072, Math.max(2, parseInt(config.num_leaves))),
            num_iterations: Math.max(1, parseInt(config.num_iterations)),
            learning_rate: parseFloat(config.learning_rate)
        };

        if (config.loadModel)
            node.config.load_from = config.loadFolder.trim();

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("lgbm", LightGBMClassifierNode);
}