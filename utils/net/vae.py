import torch
from torch import nn
from torch.nn import functional as F
from utils.net.linear.layers import fc_layer, fc_layer_split
from utils.net.linear.mlp import MLP
from utils.net.utils import device


class AutoEncoder(nn.Module):
    """Class for variational auto-encoder (VAE) models."""

    # classes parametresini sildin, gerekirse ekle
    def __init__(self, input_size=1000, z_dim=20, layers=3, hid_size=1000, hid_smooth=None,
                 drop=0, batch_norm=True, nl="leakyrelu", gated=False):
        '''Class for variational auto-encoder (VAE) models.'''


        # Optimizer (and whether it needs to be reset)
        self.optimizer = None
        self.optim_type = "adam"
        #--> self.[optim_type]   <str> name of optimizer, relevant if optimizer should be reset for every task
        self.optim_list = []
        #--> self.[optim_list]   <list>, if optimizer should be reset after each task, provide list of required <dicts>

        # Replay: temperature for distillation loss (and whether it should be used)
        self.replay_targets = "hard"  # hard|soft
        self.KD_temp = 2.

        layers = int(layers)

        # Set configurations
        super().__init__()
        self.input_size = input_size
        self.z_dim = z_dim
        self.layers = layers
        self.hid_size = hid_size
        self.hid_smooth = hid_smooth

        self.average = True #--> makes that [reconL] and [variatL] are both divided by number of input-pixels

        # Check whether there is at least 1 fc-layer
        if layers < 1:
            raise ValueError("VAE cannot have 0 fully-connected layers!")


        ######------SPECIFY MODEL------######

        ##>----Encoder (= q[z|x])----<##
        # -output size of the encoder
        encoder_output_size = input_size if layers == 1 else (hid_size if hid_smooth is None or layers < 3 else hid_smooth)
        self.encoder = MLP(input_size=input_size, output_size=encoder_output_size, layers=layers-1, hid_size=hid_size,
                           hid_smooth=hid_smooth, drop=drop, batch_norm=batch_norm, nl=nl, gated=gated)
        # -to z
        self.toZ = fc_layer_split(encoder_output_size, z_dim)

        # -from z
        self.fromZ = fc_layer(z_dim, encoder_output_size, batch_norm=layers > 1 and batch_norm, nl=nl if layers > 1 else 'none')
        
        ##>----Decoder (= p[x|z])----<##
        self.decoder = MLP(size_per_layer=self.encoder.size_per_layer[::-1], drop=drop, batch_norm=batch_norm, nl=nl, gated=gated, output='none')
        

    ##------ FORWARD FUNCTIONS --------##

    def encode(self, x):
        '''Pass input through feed-forward connections, to get [hE], [z_mean] and [z_logvar].'''
        z = self.encoder(x)
        mu, logvar = self.toZ(z)
        return mu, logvar, z


    def reparameterize(self, mu, logvar):
        '''Perform "reparametrization trick" to make these stochastic variables differentiable.'''
        std = torch.exp(0.5*logvar)     # get std from logvar
        eps = torch.randn_like(std)     # sample from normal dist. with size of std
        return mu + eps * std           # reparametrization


    def decode(self, z):
        '''Pass latent variable activations through feedback connections, to give reconstructed image [image_recon].'''
        x = self.fromZ(z)
        x = self.decoder(x)
        return x
    

    def forward(self, x, full=False, reparameterize=True):
        '''Forward function to propagate [x] through the encoder, reparametrization and decoder.

        Input:  - [x]   <4D-tensor> of shape [batch_size]x[channels]x[image_size]x[image_size]

        If [full] is True, output should be a <tuple> consisting of:
        - [x_recon]     <4D-tensor> reconstructed image (features) in same shape as [x]
        - [y_hat]       <2D-tensor> with predicted logits for each class
        - [mu]          <2D-tensor> with either [z] or the estimated mean of [z]
        - [logvar]      None or <2D-tensor> estimated log(SD^2) of [z]
        - [z]           <2D-tensor> reparameterized [z] used for reconstruction
        If [full] is False, output is simply the predicted logits (i.e., [y_hat]).'''
        # encode (forward), reparameterize and decode (backward)
        mu, logvar, z = self.encode(x)
        z = self.reparameterize(mu, logvar) if reparameterize else mu
        x_recon = self.decode(z)
        if full:
            return x_recon, mu, logvar, z
        else:
            return x_recon



    ##------ SAMPLE FUNCTIONS --------##

    def sample(self, size):
        '''Generate [size] samples from the model. Output is tensor (not "requiring grad"), on same device as <self>.'''

        # set model to eval()-mode
        mode = self.training
        self.eval()

        # sample z
        z = torch.randn(size, self.z_dim).to(device)

        # decode z into a genereated tensor
        with torch.no_grad():
            X = self.decode(z)

        # set model back to its initial mode
        self.train(mode=mode)

        # return samples as [batch_size]x[input_size] tensor
        return X



    ##------ LOSS FUNCTIONS --------##

    def calculate_recon_loss(self, x, x_recon, average=False):
        '''Calculate reconstruction loss for each element in the batch.

        INPUT:  - [x]           <tensor> with original input (1st dimension (ie, dim=0) is "batch-dimension")
                - [x_recon]     (tuple of 2x) <tensor> with reconstructed input in same shape as [x]
                - [average]     <bool>, if True, loss is average over all pixels; otherwise it is summed

        OUTPUT: - [reconL]      <1D-tensor> of length [batch_size]'''

        batch_size = x.size(0)
        reconL = F.binary_cross_entropy(input=x_recon.view(batch_size, -1), target=x.view(batch_size, -1),
                                        reduction='none')
        reconL = torch.mean(reconL, dim=1) if average else torch.sum(reconL, dim=1)

        return reconL


    def calculate_variat_loss(self, mu, logvar):
        '''Calculate reconstruction loss for each element in the batch.

        INPUT:  - [mu]        <2D-tensor> by encoder predicted mean for [z]
                - [logvar]    <2D-tensor> by encoder predicted logvar for [z]

        OUTPUT: - [variatL]   <1D-tensor> of length [batch_size]'''

        # --> calculate analytically
        # ---- see Appendix B from: Kingma & Welling (2014) Auto-Encoding Variational Bayes, ICLR ----#
        variatL = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=1)

        return variatL


    def loss_function(self, recon_x, x, y_hat=None, y_target=None, scores=None, mu=None, logvar=None):
        '''Calculate and return various losses that could be used for training and/or evaluating the model.

        INPUT:  - [recon_x]         <4D-tensor> reconstructed image in same shape as [x]
                - [x]               <4D-tensor> original image
                - [y_hat]           <2D-tensor> with predicted "logits" for each class
                - [y_target]        <1D-tensor> with target-classes (as integers)
                - [scores]          <2D-tensor> with target "logits" for each class
                - [mu]              <2D-tensor> with either [z] or the estimated mean of [z]
                - [logvar]          None or <2D-tensor> with estimated log(SD^2) of [z]

        SETTING:- [self.average]    <bool>, if True, both [reconL] and [variatL] are divided by number of input elements

        OUTPUT: - [reconL]       reconstruction loss indicating how well [x] and [x_recon] match
                - [variatL]      variational (KL-divergence) loss "indicating how normally distributed [z] is"
                - [predL]        prediction loss indicating how well targets [y] are predicted
                - [distilL]      knowledge distillation (KD) loss indicating how well the predicted "logits" ([y_hat])
                                     match the target "logits" ([scores])'''

        ###-----Reconstruction loss-----###
        reconL = self.calculate_recon_loss(x=x, x_recon=recon_x, average=self.average) #-> possibly average over pixels
        reconL = torch.mean(reconL)                                                    #-> average over batch

        ###-----Variational loss-----###
        if logvar is not None:
            variatL = self.calculate_variat_loss(mu=mu, logvar=logvar)
            variatL = torch.mean(variatL)                             #-> average over batch
            if self.average:
                variatL /= (self.image_channels * self.image_size**2) #-> divide by # of input-pixels, if [self.average]
        else:
            variatL = torch.tensor(0., device=self._device())

        ###-----Prediction loss-----###
        if y_target is not None:
            predL = F.cross_entropy(y_hat, y_target, reduction='mean')  #-> average over batch
        else:
            predL = torch.tensor(0., device=self._device())

        ###-----Distilliation loss-----###
        if scores is not None:
            n_classes_to_consider = y_hat.size(1)  #--> zeroes will be added to [scores] to make its size match [y_hat]
            distilL = utils.loss_fn_kd(scores=y_hat[:, :n_classes_to_consider], target_scores=scores, T=self.KD_temp)
        else:
            distilL = torch.tensor(0., device=self._device())

        # Return a tuple of the calculated losses
        return reconL, variatL, predL, distilL



    ##------ TRAINING FUNCTIONS --------##

    def train_a_batch(self, x, y, x_=None, y_=None, scores_=None, rnt=0.5, active_classes=None, task=1, **kwargs):
        '''Train model for one batch ([x],[y]), possibly supplemented with replayed data ([x_],[y_]).

        [x]               <tensor> batch of inputs (could be None, in which case only 'replayed' data is used)
        [y]               <tensor> batch of corresponding labels
        [x_]              None or (<list> of) <tensor> batch of replayed inputs
        [y_]              None or (<list> of) <tensor> batch of corresponding "replayed" labels
        [scores_]         None or (<list> of) <tensor> 2Dtensor:[batch]x[classes] predicted "scores"/"logits" for [x_]
        [rnt]             <number> in [0,1], relative importance of new task
        [active_classes]  None or (<list> of) <list> with "active" classes'''

        # Set model to training-mode
        self.train()

        ##--(1)-- CURRENT DATA --##
        precision = 0.
        if x is not None:
            # Run the model
            recon_batch, y_hat, mu, logvar, z = self(x, full=True)
            # If needed (e.g., Task-IL or Class-IL scenario), remove predictions for classes not in current task
            if active_classes is not None:
                y_hat = y_hat[:, active_classes[-1]] if type(active_classes[0])==list else y_hat[:, active_classes]
            # Calculate all losses
            reconL, variatL, predL, _ = self.loss_function(recon_x=recon_batch, x=x, y_hat=y_hat,
                                                           y_target=y, mu=mu, logvar=logvar)
            # Weigh losses as requested
            loss_cur = self.lamda_rcl*reconL + self.lamda_vl*variatL + self.lamda_pl*predL

            # Calculate training-precision
            if y is not None:
                _, predicted = y_hat.max(1)
                precision = (y == predicted).sum().item() / x.size(0)


        ##--(2)-- REPLAYED DATA --##
        if x_ is not None:
            # In the Task-IL scenario, [y_] or [scores_] is a list and [x_] needs to be evaluated on each of them
            # (in case of 'exact' or 'exemplar' replay, [x_] is also a list!
            TaskIL = (type(y_)==list) if (y_ is not None) else (type(scores_)==list)
            if not TaskIL:
                y_ = [y_]
                scores_ = [scores_]
                active_classes = [active_classes] if (active_classes is not None) else None
                n_replays = len(x_) if (type(x_)==list) else 1
            else:
                n_replays = len(y_) if (y_ is not None) else (len(scores_) if (scores_ is not None) else 1)

            # Prepare lists to store losses for each replay
            loss_replay = [None]*n_replays
            reconL_r = [None]*n_replays
            variatL_r = [None]*n_replays
            predL_r = [None]*n_replays
            distilL_r = [None]*n_replays

            # Run model (if [x_] is not a list with separate replay per task)
            if (not type(x_)==list):
                x_temp_ = x_
                recon_batch, y_hat_all, mu, logvar, z = self(x_temp_, full=True)

            # Loop to perform each replay
            for replay_id in range(n_replays):

                # -if [x_] is a list with separate replay per task, evaluate model on this task's replay
                if (type(x_)==list):
                    x_temp_ = x_[replay_id]
                    recon_batch, y_hat_all, mu, logvar, z = self(x_temp_, full=True)

                # If needed (e.g., Task-IL or Class-IL scenario), remove predictions for classes not in replayed task
                if active_classes is not None:
                    y_hat = y_hat_all[:, active_classes[replay_id]]
                else:
                    y_hat = y_hat_all

                # Calculate all losses
                reconL_r[replay_id], variatL_r[replay_id], predL_r[replay_id], distilL_r[replay_id] = self.loss_function(
                    recon_x=recon_batch, x=x_temp_, y_hat=y_hat,
                    y_target=y_[replay_id] if (y_ is not None) else None,
                    scores=scores_[replay_id] if (scores_ is not None) else None, mu=mu, logvar=logvar,
                )

                # Weigh losses as requested
                loss_replay[replay_id] = self.lamda_rcl*reconL_r[replay_id] + self.lamda_vl*variatL_r[replay_id]
                if self.replay_targets=="hard":
                    loss_replay[replay_id] += self.lamda_pl*predL_r[replay_id]
                elif self.replay_targets=="soft":
                    loss_replay[replay_id] += self.lamda_pl*distilL_r[replay_id]


        # Calculate total loss
        loss_replay = None if (x_ is None) else sum(loss_replay)/n_replays
        loss_total = loss_replay if (x is None) else (loss_cur if x_ is None else rnt*loss_cur+(1-rnt)*loss_replay)


        # Reset optimizer
        self.optimizer.zero_grad()
        # Backpropagate errors
        loss_total.backward()
        # Take optimization-step
        self.optimizer.step()


        # Return the dictionary with different training-loss split in categories
        return {
            'loss_total': loss_total.item(), 'precision': precision,
            'recon': reconL.item() if x is not None else 0,
            'variat': variatL.item() if x is not None else 0,
            'pred': predL.item() if x is not None else 0,
            'recon_r': sum(reconL_r).item()/n_replays if x_ is not None else 0,
            'variat_r': sum(variatL_r).item()/n_replays if x_ is not None else 0,
            'pred_r': sum(predL_r).item()/n_replays if (x_ is not None and predL_r[0] is not None) else 0,
            'distil_r': sum(distilL_r).item()/n_replays if (x_ is not None and distilL_r[0] is not None) else 0,
        }
