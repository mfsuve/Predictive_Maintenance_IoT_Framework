module.exports = function(RED) {
    function LogisticRegressionNode(config) {

        const utils = require('../../../../../utils/utils');

        var node = this;

        node.topic = 'Logistic Regression'; // TODO: topic'leri düzenle
        // Corresponding python class
        node.pynode = 'LogisticRegression';

        node.hideProcessing = true;

        node.config = {
            propagateMode: parseInt(config.propagateAfter) < 2 ? "always" : config.propagateMode,
            propagateAfter: parseInt(config.propagateAfter),
            multiclass: config.multiclass
        };

        if (config.loadModel)
            node.config.loadFrom = config.loadFolder.trim();

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("logistic_regression", LogisticRegressionNode);
}