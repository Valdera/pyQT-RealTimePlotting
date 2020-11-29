from scipy import interpolate


def interpolation_spline():
    x = np.array(x)
    y = np.array(y)
    x_smooth = np.linspace(x.min(), x.max(), 300)
    a_BSpline = interpolate.make_interp_spline(x, y)
    y_smooth = a_BSpline(x_smooth)
    return (x_smooth, y_smooth)