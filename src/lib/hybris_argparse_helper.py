import os


def add_hybris_hac_arguments(parser):
    _add_hybris_common_arguments(parser)
    parser.add_argument('--address', default=os.environ.get('HYBRIS_HAC_URL'),
                        help='HAC URL, by default using env HYBRIS_HAC_URL')


def add_hybris_hmc_arguments(parser):
    _add_hybris_common_arguments(parser)
    parser.add_argument('--address', default=os.environ.get('HYBRIS_HMC_URL'),
                        help='HMC URL, by default using env HYBRIS_HMC_URL')


def add_hybris_bo_arguments(parser):
    _add_hybris_common_arguments(parser)
    parser.add_argument('--address', default=os.environ.get('HYBRIS_BO_URL'),
                        help='BackOffice URL, by default using env HYBRIS_BO_URL')


def _add_hybris_common_arguments(parser):
    parser.add_argument('--user', default=os.environ.get('HYBRIS_USER'),
                        help='User to use to log in, by default using env HYBRIS_USER')
    parser.add_argument('--password', default=os.environ.get('HYBRIS_PASSWORD'),
                        help='Password to use to log in (leave empty for prompt), by default using env HYBRIS_PASSWORD')
