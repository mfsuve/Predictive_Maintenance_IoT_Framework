module.exports = function(RED) {
    function RandomForestNode(config) {

        const utils = require('../../../../../utils/utils');

        var node = this;

        node.topic = 'Random Forest'; // TODO: topic'leri düzenle
        // Corresponding python class
        node.pynode = 'RandomForest';

        node.hideProcessing = true;

        node.config = {
            propagateMode: parseInt(config.propagateAfter) < 2 ? "always" : config.propagateMode,
            propagateAfter: parseInt(config.propagateAfter),
            numModels: parseInt(config.numModels),
            unlimitedDepth: config.unlimitedDepth,
            maxDepth: parseInt(config.maxDepth)
        };

        if (config.loadModel)
            node.config.loadFrom = config.loadFolder.trim();

        if (config.maxFeaturesMethod == "value") {
            if (parseInt(config.maxFeaturesValue) == config.maxFeaturesValue) // if int
                node.config.maxFeatures = parseInt(config.maxFeaturesValue);
            else
                node.config.maxFeatures = parseFloat(config.maxFeaturesValue);
        } else {
            node.config.maxFeatures = config.maxFeaturesMethod;
        }

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("random_forest", RandomForestNode);
}