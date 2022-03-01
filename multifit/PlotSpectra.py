import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys

from .fitting import Spectrum

def PlotSpectra(files,title="please add title",spec_names=None):

    plt.rcParams['figure.figsize'] = [4,3]
    plt.rcParams['figure.dpi'] = 200
    plt.rcParams['lines.linewidth'] = 0.5
    plt.rcParams['text.usetex'] = True
    plt.rcParams['text.latex.preamble']=r'\usepackage{siunitx}'
    plt.rcParams['font.size'] = 5

    spectra = [Spectrum(file) for file in files]
    N_spec = len(files)

    try:
        energy_range = np.array(eval(sys.argv[1]))
    except IndexError:
        energy_range = None

    fig_all,ax_all = plt.subplots(10,1,sharex=True,figsize=(3,4))    
    cols = sns.color_palette(palette='flare',n_colors=N_spec)
    for i,(ax,col,spectrum) in enumerate(zip(ax_all,cols,spectra)):
        #fig,ax = plt.subplots(figsize=(7,3))
        Energy, counts, counts_err = spectrum(energy_range=energy_range)
        ax.step(Energy,counts,where='mid')
        ax.get_lines()[0].set_color(col)
        ax.set_ylim([min(counts),max(counts)])
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.tick_params(width=0.5,length=2)
        if spec_names is not None:
            ax.text(0.1,0.6,spec_names[i],horizontalalignment='left',verticalalignment='center',transform=ax.transAxes,color=col)


    ax_all[0].spines['top'].set_visible(True)
    ax_all[-1].spines['bottom'].set_visible(True)
    ax_all[-1].get_xaxis().set_visible(True)
    ax_all[0].set_title(title,loc='center')
    ax_all[-1].set_xlabel("Energy [keV]")
    fig_all.tight_layout()
    fig_all.subplots_adjust(hspace=0,right=0.99)
    #plt.savefig(f'/Users/johannesheines/Documents/UiO/Master/Masteroppgave/figures/Ru110spectra/frame{i}.png',format='png')

    plt.show()
