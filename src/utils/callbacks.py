from keras.callbacks import Callback, LearningRateScheduler
import numpy as np
import settings.constants as constants
import matplotlib.pyplot as plt
import os


class TrainingReferenceReconstructor(Callback):
    """
    Custom callback generating random samples using decoder during training.
    """
    def __init__(self, run_folder, execute_on, initial_epoch, vae, plot_training_loss=False):
        """
        Class constructor.
        :param run_folder: Run folder path.
        :param execute_on: Execute callback on every nth batch/epoch.
        :param initial_epoch: Initial epoch index.
        :param vae: VAE model reference.
        :param show_loss_plot: Show loss plot during training.
        """
        self.epoch = initial_epoch
        self.run_folder = run_folder
        self.execute_on = execute_on
        self.vae = vae
        self.plot_training_loss = plot_training_loss

        # Plot data references.
        self.loss = []
        self.r_loss = []
        self.kl_loss = []
        self.epochs = []

        # Prepare graphs.
        fig, axs = plt.subplot_mosaic([["Total", "Reconstruction"], ["Total", "KL"]], constrained_layout=True)
        fig.suptitle("Training Loss Evaluation", fontsize=16)
        fig.canvas.set_window_title("Training Loss Evaluation")

        self.loss_plot = axs["Total"]
        self.r_loss_plot = axs["Reconstruction"]
        self.kl_loss_plot = axs["KL"]

        plt.ion()

    def on_batch_end(self, batch_index, logs={}):
        """
        Generate reconstructed images on batch end.
        :param batch_index: Current batch index.
        :param logs: Metrics results logs.
        """
        exec_on_batch, exec_on_epoch = self.execute_on

        if batch_index % exec_on_batch == 0 and self.epoch % exec_on_epoch == 0:
            z_new = np.random.normal(size=(1, self.vae.z_dim))
            # Remove batch dim because it has only 1 item inside.
            reconstructed = self.vae.decoder.predict(np.array(z_new))[0].squeeze()

            filepath = os.path.join(
                self.run_folder, constants.SAMPLE_RESULTS_FOLDER_NAME, "img_" + str(self.epoch).zfill(3) + "_" + str(batch_index) + ".jpg"
            )
            # If no channels, make it grayscale.
            if len(reconstructed.shape) == 2:
                plt.imsave(filepath, reconstructed, cmap="gray_r")
            else:
                plt.imsave(filepath, reconstructed)

    def on_epoch_begin(self, epoch, logs={}):
        """
        Increment local epoch counter on epoch begin.
        :param epoch: Current epoch.
        :param logs: Metrics results logs.
        """
        self.epoch = epoch

    def on_epoch_end(self, epoch, logs={}):
        """
        Plot loss on epoch end.
        :param epoch: Epoch index.
        :param logs: Metric logs.
        """
        if self.plot_training_loss:
            self.loss.append(logs["loss"])
            self.r_loss.append(logs["reconstruction_loss"])
            self.kl_loss.append(logs["kl_divergence_loss"])
            self.epochs.append(epoch)

            self.loss_plot.cla()
            self.r_loss_plot.cla()
            self.kl_loss_plot.cla()

            self.loss_plot.plot(self.epochs, self.loss, label="Total loss")
            self.loss_plot.text(0.5, 0.5, str(round(logs["loss"], 3)), horizontalalignment="center", verticalalignment="center", transform=self.loss_plot.transAxes)
            self.loss_plot.legend()

            self.r_loss_plot.plot(self.epochs, self.r_loss, 'g', label="Reconstruction Loss")
            self.r_loss_plot.text(0.5, 0.5, str(round(logs["reconstruction_loss"], 3)), horizontalalignment="center", verticalalignment="center", transform=self.r_loss_plot.transAxes)
            self.r_loss_plot.legend()

            self.kl_loss_plot.plot(self.epochs, self.kl_loss, 'r', label="Gaussian Loss")
            self.kl_loss_plot.text(0.5, 0.5, str(round(logs["kl_divergence_loss"], 3)), horizontalalignment="center", verticalalignment="center", transform=self.kl_loss_plot.transAxes)
            self.kl_loss_plot.legend()

            plt.pause(0.0001)
            plt.show()


def step_decay_schedule(initial_lr, decay_factor=0.5, step_size=1):
    """
    Create Keras LearningRateScheduler to control learning rate hyper parameter during training.
    :param initial_lr: Initial learning rate.
    :param decay_factor: Decay factor.
    :param step_size: Step Size.
    :return: LearningRateScheduler instance.
    """
    def schedule(epoch):
        """
        Callback calculating new learning rate.
        :param epoch: Current epoch.
        :return: New Learning rate.
        """
        new_lr = initial_lr * (decay_factor ** np.floor(epoch / step_size))
        return new_lr

    return LearningRateScheduler(schedule)
