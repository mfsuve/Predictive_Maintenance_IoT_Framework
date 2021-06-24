module.exports = function(RED) {
    function GaussianNaiveBayesNode(config) {

        const utils = require('../../../../../utils/utils');

        var node = this;

        node.topic = 'Gaussian Naive Bayes'; // TODO: topic'leri düzenle
        // Corresponding python class
        node.pynode = 'GaussianNaiveBayes';

        node.hideProcessing = true;

        node.config = {
            propagateMode: parseInt(config.propagateAfter) < 2 ? "always" : config.propagateMode,
            propagateAfter: parseInt(config.propagateAfter)
        };

        if (config.loadModel)
            node.config.loadFrom = config.loadFolder.trim();

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("gaussian_nb", GaussianNaiveBayesNode);
}