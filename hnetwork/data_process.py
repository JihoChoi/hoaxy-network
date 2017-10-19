import logging
from os.path import join, splitext, basename

import pandas as pd
import networkx as nx
import numpy as np

from . import BASE_DIR

logger = logging.getLogger()

DATA_DIR = join(BASE_DIR, 'data')
PLOTS_DIR = join(BASE_DIR, 'plots')


def get_data_file(fn):
    return join(DATA_DIR, fn)


def get_out_file(fn):
    return join(PLOTS_DIR, fn)


def get_absprefix(abspath):
    root, ext = splitext(abspath)
    return root


def nplog(a, base):
    return np.log(a)/np.log(base)


def ccdf(s):
    """
    Parameters:
        `s`, series, the values of s should be variable to be handled
    Return:
        a new series `s`, index of s will be X axis (number), value of s
        will be Y axis (probability)
    """
    s = s.copy()
    s = s.sort_values(ascending=True, inplace=False)
    s.reset_index(drop=True, inplace=True)
    n = len(s)
    s.drop_duplicates(keep='first', inplace=True)
    X = s.values
    Y = [n - i for i in s.index]

    return pd.Series(data=Y, index=X) / n


def decompose_network(fn):
    """Return the decomposed network by site_type."""
    fn = get_data_file(fn)
    logger.info('Raw network file is: %r', fn)
    logger.info('Decomposing ...')
    fbn, fext = splitext(basename(fn))
    fn_fn = get_data_file(fbn + '.fn.csv')
    ff_fn = get_data_file(fbn + '.fc.csv')
    df = pd.read_csv(fn)
    if 'from_indexed_id' in df.columns:
        df = df.drop('from_indexed_id', axis=1)
    if 'to_indexed_id' in df.columns:
        df = df.drop('to_indexed_id', axis=1)
    fn_df = df.loc[df.cweight > 0].copy()
    fn_df = fn_df.drop('fweight', axis=1).rename(
            columns=dict(cweight='weight'))
    ff_df = df.loc[df.fweight > 0].copy()
    ff_df = ff_df.drop('cweight', axis=1).rename(
            columns=dict(fweight='weight'))
    logger.info('Saving fake news network to %r ...', fn_fn)
    fn_df.to_csv(fn_fn, index=False)
    logger.info('Saving fact checking network to %r ...', ff_fn)
    ff_df.to_csv(ff_fn, index=False)


def index_edge_list(ifn, ofn, ikwargs=dict(), okwargs=dict(index=False)):
    df = pd.read_csv(ifn, **ikwargs)
    s = pd.concat((df[df.columns[0]], df[df.columns[1]]))
    s = s.drop_duplicates()
    s = s.sort_values().reset_index(drop=True)
    s = {v:k for k, v in s.to_dict().items()}
    df['from_idx'] = df[df.columns[0]].apply(s.get)
    df['to_idx'] = df[df.columns[1]].apply(s.get)
    df = df.sort_values(['from_idx', 'to_idx'])
    df[['from_idx', 'to_idx']].to_csv(ofn, **okwargs)


def rearrange_ranked_centralities(fn='centralities.20.raw.csv'):
    df = pd.read_csv(fn)
    data = []
    for c in df.columns:
        data += [(i, c, v) for i, v in df[c].iteritems()]
    ndf = pd.DataFrame(data, columns=['rank', 'centrality', 'screen_name'])
    ndf.to_csv('centralities.20.csv', index=False)


def rank_centralities(fn1='centralities.raw.csv',
                      fn2='retweet.1108.claim.vmap.csv'):
    df = pd.read_csv(fn1)
    vmap = pd.read_csv(fn2)
    vmap = vmap.raw_id
    df = df.sort_values('in_degree', ascending=False)
    ranked_ki = df.screen_name.values.copy()
    ranked_kii = vmap.loc[df.index.tolist()].values.copy()
    ranked_kiv = df.in_degree.values.copy()
    df = df.sort_values('out_degree', ascending=False)
    ranked_ko = df.screen_name.values.copy()
    ranked_koi = vmap.loc[df.index.tolist()].values.copy()
    ranked_kov = df.out_degree.values.copy()
    df = df.sort_values('weighted_in_degree', ascending=False)
    ranked_si = df.screen_name.values.copy()
    ranked_sii = vmap.loc[df.index.tolist()].values.copy()
    ranked_siv = df.weighted_in_degree.values.copy()
    df = df.sort_values('weighted_out_degree', ascending=False)
    ranked_so = df.screen_name.values.copy()
    ranked_soi = vmap.loc[df.index.tolist()].values.copy()
    ranked_sov = df.weighted_out_degree.values.copy()
    df = df.sort_values('page_rank', ascending=False)
    ranked_pr = df.screen_name.values.copy()
    ranked_pri = vmap.loc[df.index.tolist()].values.copy()
    ranked_prv = df.page_rank.values.copy()
    df = df.sort_values('betweenness', ascending=False)
    ranked_bt = df.screen_name.values.copy()
    ranked_bti = vmap.loc[df.index.tolist()].values.copy()
    ranked_btv = df.betweenness.values.copy()
    df = df.sort_values('eigenvector', ascending=False)
    ranked_ev = df.screen_name.values.copy()
    ranked_evi = vmap.loc[df.index.tolist()].values.copy()
    ranked_evv = df.eigenvector.values.copy()
    ranked_df_sn = pd.DataFrame(
        dict(
            in_degree=ranked_ki,
            out_degree=ranked_ko,
            weighted_in_degree=ranked_si,
            weighted_out_degree=ranked_so,
            page_rank=ranked_pr,
            betweenness=ranked_bt,
            eigenvector=ranked_ev))
    ranked_df_sn.to_csv('centralities.ranked.screen_name.csv', index=False)
    ranked_df_id = pd.DataFrame(
        dict(
            in_degree=ranked_kii,
            out_degree=ranked_koi,
            weighted_in_degree=ranked_sii,
            weighted_out_degree=ranked_soi,
            page_rank=ranked_pri,
            betweenness=ranked_bti,
            eigenvector=ranked_evi))
    ranked_df_id.to_csv('centralities.ranked.raw_id.csv', index=False)
    ranked_df_v = pd.DataFrame(
        dict(
            in_degree=ranked_kiv,
            out_degree=ranked_kov,
            weighted_in_degree=ranked_siv,
            weighted_out_degree=ranked_sov,
            page_rank=ranked_prv,
            betweenness=ranked_btv,
            eigenvector=ranked_evv))
    ranked_df_v.to_csv('centralities.ranked.values.csv', index=False)


def changes_of_cores(fn1='k_core_evolution.csv',
                     fn2='vertex_map.csv'):
    """The changes of mcores by intersection daily."""
    df1 = pd.read_csv(fn1, parse_dates=['timeline'])
    df2 = pd.read_csv(fn2, header=None)
    df2.columns = ['raw_id', 'v_idx']
    df2 = df2.set_index('v_idx')
    df1['mcore_idx'] = df1.mcore_idx.apply(eval).apply(set)
    df1 = df1.set_index('timeline')
    s1 = df1.loc['2016-11-07', 'mcore_idx'].iloc[0]
    s2 = set(s1)
    for ts, s0 in df1.mcore_idx.loc['2016-11-08':].iteritems():
        s1 &= s0
        s2 |= s0
    unchanged = df2.loc[list(s1)]
    unions = df2.loc[list(s2)]
    unchanged.to_csv('k_core.daily.intersection.csv')
    unions.to_csv('k_core.daily.union.csv')
    logger.info('Number of unchanged is %s', len(unchanged))
    logger.info('Number of union is %s', len(unions))


def rank_correlation_bot_centrality(top=1000,
                        fn1='ubs.csv',
                        fn2='centralities.ranked.raw_id.csv',
                        fn3='centralities.ranked.values.csv'):
    if top > 1000:
        raise ValueError('Top should not larger than 1000!')
    df1 = pd.read_csv(fn1)
    bmap = df1.set_index('user_raw_id').bot_score_en
    df2 = pd.read_csv(fn2)
    df3 = pd.read_csv(fn3)
    df2 = df2.iloc[:top]
    df3 = df3.iloc[:top]
    spearmans = []
    kendalls = []
    for c in df3.columns:
        bs = bmap.loc[df2[c].values]
        df = pd.DataFrame(
            dict(centrality=df3[c].values.copy(), bot_score=bs.values.copy()))
        df = df.loc[df.bot_score.notnull()]
        a1 = df.centrality.values
        a2 = df.bot_score.values
        rho, rhop = spearmanr(a1, a2)
        tau, taup = kendalltau(a1, a2)
        spearmans.append((c, 'spearmanr', rho, rhop))
        kendalls.append((c, 'kendalltau', tau, taup))
    df = pd.DataFrame(spearmans)
    df.to_csv('rank_correlation_bot_centrality.spearman.{}.csv'.format(top),
              index=False)
    df = pd.DataFrame(kendalls)
    df.to_csv('rank_correlation_bot_centrality.kendall.{}.csv'.format(top),
              index=False)



