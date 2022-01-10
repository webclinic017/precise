
# Ack: https://carstenschelp.github.io/2019/05/12/Online_Covariance_Algorithm_002.html
import numpy as np
from precise.precision.fixed import fixed_rpre_init, fixed_rpre_update
from precise.covariance.util import multiply_diag, normalize, grand_shrink
from precise.covariance.generate import create_correlated_dataset, create_factor_dataset, create_disjoint_dataset, create_band_dataset
from pprint import pprint
from precise.covariance.adjacency import infer_adjacency
import random


def test_fixed_rpre_init():
    if True:
        n_clusters = 30
        n_per_group = 5
        n_dims = [ random.choice([n_per_group]) for _ in range(n_clusters)]
        big_data = create_disjoint_dataset(n=10000, n_dims=n_dims)
    else:
        n_dim = 100
        big_data = create_band_dataset(n=10000, n_dim=n_dim, n_bands=3)
        n_per_group = 2
    true_cov = np.cov(big_data, rowvar=False)
    true_pre = np.linalg.inv(true_cov)


    phi = 1.1
    n_small=240
    small_data = big_data[:n_small,:]
    small_cov = np.cov(small_data,rowvar=False)
    small_pre = np.linalg.inv(multiply_diag(small_cov, phi=phi))
    adj = infer_adjacency(small_pre)
    
    n_tiny = 24
    tiny_data = big_data[:n_tiny]
    emp_cov = np.cov(tiny_data, rowvar=False)
    phi = 1.3
    lmbd = 0.75
    ridge_cov = multiply_diag(emp_cov, phi=phi, make_copy=True)
    affine_cov = grand_shrink(ridge_cov, lmbd=lmbd, make_copy=True)
    shrink_cov = grand_shrink(emp_cov, lmbd=lmbd, make_copy=True)
    ridge_pre = np.linalg.inv(ridge_cov)
    shrink_pre = np.linalg.inv(shrink_cov)
    affine_pre = np.linalg.inv(affine_cov)

    rho = 1/n_tiny
    phi = 1.3
    lmbd = 0.75
    pre = fixed_rpre_init(adj=adj, rho=rho, n_emp=n_tiny)
    for x in tiny_data[:-1,:]:
        pre = fixed_rpre_update(m=pre, x=x, with_precision=False, lmbd=lmbd, phi=phi)
    pre = fixed_rpre_update(m=pre, x=tiny_data[-1,:], with_precision=True, lmbd=lmbd, phi=phi)

    block_pre = pre['pre']
    # block_cov = np.linalg.inv(block_pre)
    
    # Portfolios
    n_dim = np.shape(big_data)[1]
    wones = np.ones(shape=(n_dim,1))
    w_block = normalize( np.squeeze(np.matmul( pre['pre'],wones )) )
    w_ridge = normalize( np.squeeze(np.matmul( ridge_pre, wones)))
    w_affine = normalize(np.squeeze(np.matmul(affine_pre, wones)))
    w_shrink = normalize(np.squeeze(np.matmul( shrink_pre, wones)))
    w_perfect = normalize( np.squeeze(np.matmul( true_pre, wones)))
    import matplotlib.pyplot as plt
    descreasing = list(range(len(w_block),0,-1))


    w_uniform = np.ones(shape=(n_dim,1))/n_dim
    true_var_uniform = np.matmul(np.matmul( w_uniform.T, true_cov), w_uniform)[0,0]
    true_var_block = np.matmul(np.matmul( w_block.T, true_cov), w_block)
    true_var_shrink = np.matmul(np.matmul(w_shrink.T, true_cov), w_shrink)
    true_var_ridge = np.matmul(np.matmul( w_ridge.T, true_cov), w_ridge)
    true_var_perfect = np.matmul(np.matmul(w_perfect.T, true_cov), w_perfect)
    true_var_affine = np.matmul(np.matmul(w_affine.T, true_cov), w_affine)

    uniform_var_ratio = true_var_uniform/true_var_perfect
    block_var_ratio = true_var_block/true_var_perfect
    ridge_var_ratio = true_var_ridge/true_var_perfect
    shrink_var_ratio = true_var_shrink / true_var_perfect
    affine_var_ratio = true_var_affine / true_var_perfect

    plt.plot(descreasing, w_uniform,
             descreasing,sorted(w_block,reverse=True),
             descreasing, sorted(w_affine, reverse=True),
             descreasing, sorted(w_ridge,reverse=True),
             descreasing, sorted(w_shrink,reverse=True),
             descreasing, sorted(w_perfect,reverse=True))
    plt.grid()
    plt.ylabel('Portfolio weight')
    plt.xlabel('Asset number')
    plt.title('Porfolio Variance ('+str(n_per_group)+' per group)')
    plt.legend(['uniform '+str(uniform_var_ratio),
                'affine ' + str(affine_var_ratio),
                'block '+str(block_var_ratio),
                'ridge '+str(ridge_var_ratio),
                'shrink '+str(shrink_var_ratio),
                'perfect '+str(1)])
    plt.show()


    ridge_pre_error = np.linalg.norm(ridge_pre-true_pre)
    block_pre_error = np.linalg.norm(block_pre-true_pre)
    affine_pre_error = np.linalg.norm(affine_pre - true_pre)

    leaderboard =  sorted([ (block_var_ratio,'block_ratio'),
                     (uniform_var_ratio,'uniform_ratio'),
                     (ridge_var_ratio,'ridge_ratio'),
                     (shrink_var_ratio,'shrink_var_ratio') ])


    if true_var_block < min( true_var_ridge, true_var_uniform):
        print('*** BETTER ***')
    else:
        print('*** WORSE ***')
    pprint(leaderboard)
    print('---------------')
    from collections import OrderedDict
    report = OrderedDict({'optimal_var':true_var_perfect,'uniform_var':true_var_uniform,'block_var':true_var_block,'ridge_var':true_var_ridge,
              'block_ratio':block_var_ratio, 'uniform_ratio':uniform_var_ratio,
                          'ridge_ratio':ridge_var_ratio,'shrink_var_ratio':shrink_var_ratio,
              'block_pre_norm':block_pre_error,'ridge_pre_norm':ridge_pre_error,'affine_pre_norm':affine_pre_error,
              'w1':w_block[:10],'w2':w_ridge[:10],'wt':w_perfect[:10]})
    pprint(report)
    if False:
        print('---implied sgma-')
        pprint(block_cov[:5,:5])
        print('---true sgma-')
        pprint(true_cov[:5,:5])
        print('---conventional-')
        pprint(emp_cov[:5,:5])
        print('---block precision---')
        pprint(pre['pre'])
        print('---true precision---')
        pprint(np.linalg.inv(true_cov[:5,:5]))
        print('---conv precision---')
        pprint(ridge_pre[:5,:5])


if __name__=='__main__':
    test_fixed_rpre_init()
