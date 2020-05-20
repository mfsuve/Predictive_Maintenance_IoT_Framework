module.exports = function(RED) {
    function StandardScalerNode(config) {
        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'data';

        node.config = {
            // Corresponding python node
            pyfunc: 'StandardScaler'
        };

        utils.run(RED, node, config);
    }
    RED.nodes.registerType('standard scaler', StandardScalerNode);
}