module.exports = function(RED) {
    function StandardScalerNode(config) {
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';

        node.config = {
            // Corresponding python function
            pyfunc: 'standard_scaler'
        };

        utils.run(RED, node, config);
    }
    RED.nodes.registerType('standard scaler', StandardScalerNode);
}