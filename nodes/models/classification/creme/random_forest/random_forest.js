module.exports = function(RED) {
    function RandomForestNode(config) {

        const utils = require('../../../../../utils/utils');

        var node = this;

        node.topic = 'Random Forest'; // TODO: topic'leri düzenle
        // Corresponding python class
        node.pynode = 'RandomForest';

        node.hideProcessing = true;

        node.config = {};

        if (config.loadModel)
            node.config.loadFrom = config.loadFolder.trim();

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("random_forest", RandomForestNode);
}