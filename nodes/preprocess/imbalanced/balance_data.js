module.exports = function(RED) {
    function BalanceDataNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'BalanceData';

        node.config = {
            sampling_type: config.balanceData || "combine SMOTEENN"
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("balance_data", BalanceDataNode);
}