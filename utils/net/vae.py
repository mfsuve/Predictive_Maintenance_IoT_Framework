from utils.utils import myprint as print

import torch
from torch import nn
from torch.nn import functional as F
from utils.net.linear.layers import fc_layer, fc_layer_split
from utils.net.linear.mlp import MLP
from utils.net.utils import Trainable, device


class AutoEncoder(Trainable):
    """Class for variational auto-encoder (VAE) models."""

    # classes parametresini sildin, gerekirse ekle
    def __init__(self, input_size=1000, z_dim=20, layers=3, hid_size=1000, hid_smooth=None,
                 drop=0, batch_norm=True, nl="leakyrelu", gated=False):
        '''Class for variational auto-encoder (VAE) models.'''

        super().__init__()
        
        layers = int(layers)
        if layers < 1:
            raise ValueError("VAE cannot have 0 fully-connected layers!")

        self.z_dim = z_dim

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
    

    def forward(self, x):
        '''Forward function to propagate [x] through the encoder, reparametrization and decoder.'''
        # encode (forward), reparameterize and decode (backward)
        mu, logvar, z = self.encode(x)
        z = self.reparameterize(mu, logvar)
        x_recon = self.decode(z)
        return x_recon, mu, logvar, z



    ##------ SAMPLE FUNCTIONS --------##

    def sample(self, size):
        '''Generate [size] samples from the model. Output is tensor (not "requiring grad"), on same device as <self>.'''

        mode = self.training
        self.eval()

        z = torch.randn(size, self.z_dim).to(device)
        with torch.no_grad():
            X = self.decode(z)

        self.train(mode=mode)

        return X



    ##------ LOSS FUNCTIONS --------##

    def recon_loss(self, x, x_recon):
        return F.binary_cross_entropy(x_recon, x, reduction='none').mean(dim=1)


    def variat_loss(self, mu, logvar):
        return -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=1)


    def loss(self, x, x_recon, mu, logvar):
        recon_loss = self.recon_loss(x, x_recon).mean()
        variat_loss = self.variat_loss(mu, logvar).mean()
        variat_loss /= x.size()[1]

        return recon_loss + variat_loss


    ##------ TRAINING FUNCTIONS --------##

    def train_step(self, x, y, gen_x, gen_y, scores, gen_scores, rnt):
        super().train_step()

        x_recon, mu, logvar, z = self(x)
        total_loss = self.loss(x, x_recon, mu, logvar)
        
        if gen_x is not None:
            gen_x_recon, mu, logvar, z = self(gen_x)
            replay_loss = self.loss(gen_x, gen_x_recon, mu, logvar)
            total_loss = rnt * total_loss + (1 - rnt) * replay_loss

        total_loss.backward()
        self.optimizer.step()
