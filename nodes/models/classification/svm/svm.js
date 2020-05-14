module.exports = function(RED) {
    function SVMNode(config) {

        const path = require('path');
        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'model';
        // Does node have error output
        // node.haserror = true;

        node.config = {
            // Corresponding python function
            pyfunc: 'svm',
            kernel: config.kernel,
            degree: Math.max(1, parseInt(config.degree)),
            C: Math.max(0.000001, parseFloat(config.C)),
            gammaSelect: config.gammaSelect,
            gamma: parseFloat(config.gamma),
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("svm", SVMNode);
}