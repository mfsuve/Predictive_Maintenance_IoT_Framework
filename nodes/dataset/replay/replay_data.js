module.exports = function(RED) {
    function ReplayDataNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';

        node.hideProcessing = true;

        node.config = {
            // Corresponding python class
            pynode: 'ReplayData',
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("replay data", ReplayDataNode);
}