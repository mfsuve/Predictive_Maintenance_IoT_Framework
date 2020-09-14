module.exports = function(RED) {
    function ReplayDataNode(config) {

        const path = require('path');
        const utils = require('../../../utils/utils');

        var node = this;

        node.topic = 'data';
        // Corresponding python class
        node.pynode = 'ReplayData';

        node.hideProcessing = true;

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("replay data", ReplayDataNode);
}