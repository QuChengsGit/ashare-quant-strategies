def before_market_open(context):
    if g.wait_list:
        optimized_weight = portfolio_optimizer(
            date=context.previous_date,
            securities=g.wait_list,
            target=MinVariance(count=240),
            constraints=[WeightConstraint(low=0.9, high=1.0)],
            bounds=[],
            default_port_weight_range=[0., 1.0],
            ftol=1e-09,
            return_none_if_fail=True
        )
        print(optimized_weight)
        g.buy = optimized_weight.sort_values(ascending=False)
    else:
        g.buy = pd.Series(dtype=float)

复制
