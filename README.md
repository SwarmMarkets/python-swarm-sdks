# Swarm Collection - Python SDK Suite

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Package Version](https://img.shields.io/badge/version-1.0.0b1-orange.svg)](https://pypi.org/project/swarm-collection/)

> **Unified Python SDK collection for trading Real World Assets (RWAs) across multiple platforms with smart routing, automatic fallback, and price optimization.**

---

## 📋 Table of Contents

- [Overview](#-overview)
- [SDK Architecture](#-sdk-architecture)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Installation & Setup](#-installation--setup)
- [SDK Descriptions](#-sdk-descriptions)
- [Project Structure](#-project-structure)
- [Development Setup](#-development-setup)
- [Deployment & CI/CD](#-deployment--cicd)
- [Documentation](#-documentation)
- [Examples](#-examples)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**Swarm Collection** is a comprehensive Python SDK suite that enables seamless trading of Real World Assets (RWAs) through multiple platforms. The collection provides three distinct SDKs, each optimized for different trading scenarios:

1. **Trading SDK** - Unified client with smart routing and automatic price optimization
2. **Market Maker SDK** - Decentralized peer-to-peer OTC trading (24/7 availability)
3. **Cross-Chain Access SDK** - Centralized stock market trading (market hours only)

All SDKs share common infrastructure including Web3 helpers, authentication, and data models, ensuring consistent behavior and ease of use.

### Why Use Swarm Collection?

- ✅ **Smart Routing** - Automatically selects optimal trading platform
- ✅ **Best Price Guarantee** - Real-time price comparison across platforms
- ✅ **Auto Fallback** - Seamless switching if primary platform fails
- ✅ **24/7 Trading** - Access to P2P markets outside traditional hours
- ✅ **Unified API** - Consistent interface across all SDKs
- ✅ **Production Ready** - Comprehensive error handling and retry logic
- ✅ **Type Safe** - Full type hints and mypy validation
- ✅ **Async Native** - Built with asyncio for high performance

---

## 🏗️ SDK Architecture

The Swarm Collection implements a **multi-layer hierarchical architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                      Trading SDK                            │
│  (Smart routing, price comparison, auto-fallback)           │
└───────────────┬───────────────────────────┬─────────────────┘
                │                           │
      ┌─────────▼──────────┐      ┌────────▼─────────────┐
      │  Market Maker SDK  │      │ Cross-Chain Access   │
      │  (P2P, 24/7)       │      │ SDK (Stock market)   │
      └─────────┬──────────┘      └────────┬─────────────┘
                │                           │
                └────────────┬──────────────┘
                             │
                    ┌────────▼─────────┐
                    │   Shared Module  │
                    │ (Web3, Auth, etc)│
                    └──────────────────┘
```

### Layer Responsibilities

| Layer                      | Purpose                              | Key Components                                         |
| -------------------------- | ------------------------------------ | ------------------------------------------------------ |
| **Trading SDK**            | Unified interface with smart routing | `TradingClient`, `Router`, routing strategies          |
| **Market Maker SDK**       | P2P on-chain trading                 | `RPQClient`, `MarketMakerWeb3Client`, offer management |
| **Cross-Chain Access SDK** | Stock market integration             | `CrossChainAccessAPIClient`, market hours validation   |
| **Shared Module**          | Common infrastructure                | `Web3Helper`, `SwarmAuth`, `BaseClient`, models        |

---

## 🎯 Key Features

### Trading SDK (Highest Level)

- **5 Routing Strategies**: BEST_PRICE, CROSS_CHAIN_ACCESS_FIRST, MARKET_MAKER_FIRST, CROSS_CHAIN_ACCESS_ONLY, MARKET_MAKER_ONLY
- **Automatic Price Comparison**: Real-time quote aggregation from both platforms
- **Smart Fallback**: Automatic retry on alternative platform if primary fails
- **Unified Interface**: Single `trade()` method works across all platforms
- **Platform-Aware**: Handles market hours, liquidity checks, and platform-specific requirements

### Market Maker SDK

- **24/7 Availability**: Trade anytime, no market hour restrictions
- **P2P On-Chain**: Fully decentralized execution via smart contracts
- **Offer Discovery**: RPQ API integration for finding available liquidity
- **Create Offers**: Become a liquidity provider with custom pricing
- **Dynamic Pricing**: Support for price feed-based offers
- **Quote Calculation**: Best offer selection with amount optimization

### Cross-Chain Access SDK

- **Stock Market Pricing**: Real US stock exchange rates
- **Deep Liquidity**: Traditional market maker liquidity
- **Market Hours Validation**: 14:30-21:00 UTC, weekdays only
- **Account Management**: Funds tracking and status checks
- **Email Notifications**: Trade confirmation emails
- **KYC Compliant**: Regulatory requirements handled

### Shared Infrastructure

- **Web3 Operations**: Token approvals, balance checks, transaction signing
- **Wallet Authentication**: EIP-191 signature-based auth (no passwords)
- **Multi-Network**: Polygon, Ethereum, Arbitrum, Base, Optimism support
- **HTTP Client**: Automatic retries with exponential backoff
- **Error Handling**: Comprehensive exception hierarchy
- **Remote Config**: Dynamic configuration loading from remote URLs

---

## 🚀 Quick Start

```bash
# Install the package
pip install swarm-collection

# Import and use
from swarm.trading_sdk import TradingClient
from swarm.shared.models import Network
```

For detailed usage examples and code samples, see:

- [Trading SDK Documentation](docs/trading_sdk_doc.md)
- [Market Maker SDK Documentation](docs/market_maker_sdk_doc.md)
- [Cross-Chain Access SDK Documentation](docs/cross_chain_access_sdk_doc.md)
- [Examples Directory](examples/)

---

## 📦 Installation & Setup

### Prerequisites

- **Python 3.8 or higher**
- **pip** (Python package manager)
- **Wallet with private key** (for transaction signing)
- **Gas tokens** (MATIC, ETH, etc. for transaction fees)
- **RPQ API Key** (for Market Maker SDK access)
- **User Email** (for Cross-Chain Access authentication)

### Method 1: Install from PyPI (Production)

```bash
pip install swarm-collection
```

### Method 2: Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/SwarmMarkets/python-swarm-sdks.git
cd python-swarm-sdks

# Install in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Environment Configuration

⚠️ **Important**: The `.env` file is **only required for running the examples**, not for using the SDKs in your own projects. When integrating the SDKs into your application, pass credentials directly to the client constructors.

#### For Running Examples Only

If you want to run the provided examples, create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Then configure your environment variables in the `.env` file:

```bash
# Required: Your wallet private key (with 0x prefix)
PRIVATE_KEY=0x1234567890123456789012345678901234567890123456789012345678901234

# Required for Cross-Chain Access SDK and Trading SDK
USER_EMAIL=your@email.com

# Required for Market Maker SDK and Trading SDK
RPQ_API_KEY=your-rpq-api-key-here

# Optional: Environment mode (dev or prod, defaults to prod)
SWARM_COLLECTION_MODE=prod

# Optional: Custom RPC endpoint
# RPC_URL=https://polygon-rpc.com

# Optional: Remote configuration URLs (for dynamic config loading)
# SWARM_CONFIG_PROD_URL=https://your-storage.com/config.prod.json
# SWARM_CONFIG_DEV_URL=https://your-storage.com/config.dev.json
```

#### For SDK Integration in Your Projects

When using the SDKs in your own code, pass credentials directly to the client:

```python
from swarm.trading_sdk import TradingClient
from swarm.shared.models import Network

# Pass credentials directly - no .env file needed
async with TradingClient(
    network=Network.POLYGON,
    private_key="0x...",           # Your private key
    rpq_api_key="your_rpq_key",    # Your RPQ API key
    user_email="you@example.com"   # Your email
) as client:
    # Use the client
    pass
```

⚠️ **Security Note**: Never commit your `.env` file or private keys to version control!

---

## 📚 SDK Descriptions

### 1. Trading SDK - Unified Smart Routing

**Highest-level interface** that intelligently combines both Market Maker and Cross-Chain Access platforms with automatic routing, price comparison, and fallback protection.

**Best for**: Production applications, traders seeking optimal prices and reliability

**Key Features**: 5 routing strategies, real-time price comparison, automatic fallback, unified API

📖 [User Guide](docs/trading_sdk_doc.md) | [API Reference](docs/trading_sdk_api.md)

---

### 2. Market Maker SDK - Decentralized P2P Trading

**Decentralized on-chain trading** through smart contract-based offers with 24/7 availability and permissionless access.

**Best for**: Market makers, liquidity providers, 24/7 trading, DeFi applications

**Key Features**: P2P execution, create/manage offers, fixed & dynamic pricing, no KYC required

📖 [User Guide](docs/market_maker_sdk_doc.md) | [API Reference](docs/market_maker_sdk_api.md)

---

### 3. Cross-Chain Access SDK - Stock Market Integration

**Centralized stock market trading** with real US stock exchange rates and traditional market liquidity.

**Best for**: Stock trading apps, regulated services, traditional finance integration

**Key Features**: Stock market pricing, deep liquidity, market hours (14:30-21:00 UTC), KYC compliant

⚠️ **Requires**: KYC verification at [https://dotc.eth.limo/](https://dotc.eth.limo/)

📖 [User Guide](docs/cross_chain_access_sdk_doc.md) | [API Reference](docs/cross_chain_access_sdk_api.md)

---

## 📂 Project Structure

```
python-swarm-sdks/
├── swarm/                          # Main package
│   ├── __init__.py                # Package initialization
│   │
│   ├── trading_sdk/               # Trading SDK (Layer 1)
│   │   ├── sdk/
│   │   │   └── client.py          # TradingClient - unified interface
│   │   ├── routing.py             # Smart routing logic & strategies
│   │   └── exceptions.py          # Trading-specific exceptions
│   │
│   ├── market_maker_sdk/          # Market Maker SDK (Layer 2a)
│   │   ├── sdk/
│   │   │   └── client.py          # MarketMakerClient - main interface
│   │   ├── rpq_service/           # RPQ API integration
│   │   │   ├── client.py          # Offer discovery & quotes
│   │   │   ├── models.py          # Offer data models
│   │   │   └── exceptions.py     # RPQ-specific exceptions
│   │   ├── market_maker_web3/     # On-chain execution
│   │   │   ├── client.py          # Smart contract interactions
│   │   │   ├── constants.py       # Contract addresses & ABIs
│   │   │   └── exceptions.py     # Web3-specific exceptions
│   │   └── __init__.py
│   │
│   ├── cross_chain_access_sdk/    # Cross-Chain Access SDK (Layer 2b)
│   │   ├── sdk/
│   │   │   └── client.py          # CrossChainAccessClient - main interface
│   │   ├── cross_chain_access/    # API integration
│   │   │   ├── client.py          # HTTP API client
│   │   │   ├── models.py          # Quote & order models
│   │   │   └── exceptions.py     # API-specific exceptions
│   │   ├── market_hours/          # Market hours validation
│   │   │   └── market_hours.py   # Trading hours logic
│   │   └── __init__.py
│   │
│   └── shared/                    # Shared infrastructure (Layer 3)
│       ├── base_client.py         # HTTP client with retries
│       ├── swarm_auth.py          # Wallet-based authentication
│       ├── models.py              # Common data models (Network, Quote, etc)
│       ├── constants.py           # Token addresses, RPC URLs
│       ├── config.py              # Environment configuration
│       ├── remote_config.py       # Remote config loader
│       └── web3/
│           ├── helpers.py         # Web3 operations (approvals, txs)
│           ├── constants.py       # Network configs, ABIs
│           └── exceptions.py     # Web3 exceptions
│
├── examples/                      # Usage examples
│   ├── example_trading.py         # Trading SDK demo
│   ├── example_market_maker.py    # Market Maker SDK demo
│   ├── example_cross_chain_access.py  # Cross-Chain Access SDK demo
│   ├── example_error_handling.py  # Error handling patterns
│   └── README.md                  # Examples documentation
│
├── docs/                          # Documentation
│   ├── README.md                  # Documentation index
│   ├── trading_sdk_doc.md         # Trading SDK user guide
│   ├── trading_sdk_api.md         # Trading SDK API reference
│   ├── market_maker_sdk_doc.md    # Market Maker SDK user guide
│   ├── market_maker_sdk_api.md    # Market Maker SDK API reference
│   ├── cross_chain_access_sdk_doc.md     # Cross-Chain Access SDK user guide
│   └── cross_chain_access_sdk_api.md     # Cross-Chain Access SDK API reference
│
├── .github/                       # GitHub configuration
│   ├── workflows/
│   │   └── publish.yaml          # CI/CD pipeline for PyPI publishing
│   └── copilot-instructions.md   # AI assistant instructions
│
├── config.dev.json                # Development environment config
├── config.prod.json               # Production environment config
├── pyproject.toml                 # Project metadata & dependencies
├── Makefile                       # Development commands
├── MANIFEST.in                    # Package manifest
├── LICENSE                        # Apache 2.0 license
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

### Key Directories

| Directory                       | Purpose                                     |
| ------------------------------- | ------------------------------------------- |
| `swarm/trading_sdk/`            | Smart routing and unified trading interface |
| `swarm/market_maker_sdk/`       | P2P on-chain trading implementation         |
| `swarm/cross_chain_access_sdk/` | Stock market API integration                |
| `swarm/shared/`                 | Common utilities used by all SDKs           |
| `examples/`                     | Complete working examples for each SDK      |
| `docs/`                         | User guides and API references              |
| `.github/workflows/`            | CI/CD pipelines and automation              |

---

## 🛠️ Development Setup

### Setting Up Virtual Environment

The project uses Python virtual environments for dependency isolation. Follow these steps:

#### Method 1: Using Makefile (Recommended)

```bash
# Setup venv and install package with dev dependencies
make setup

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate   # On Windows

# Verify installation
python -c "import swarm; print(swarm.__version__)"
```

#### Method 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate   # On Windows

# Upgrade pip
pip install --upgrade pip

# Install package in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Development Commands

The project includes a comprehensive Makefile with common development tasks:

```bash
# Show all available commands
make help

# Installation
make install         # Install package (production mode)
make install-dev     # Install with dev dependencies

# Code Quality
make format          # Format code with black & isort
make lint            # Run flake8 & mypy
make clean           # Remove build artifacts and cache

# Building
make build           # Build distribution packages (sdist, wheel)

# Publishing
make upload          # Upload to PyPI (production)
make upload-test     # Upload to TestPyPI (testing)

# Running Examples
make example-trading              # Run Trading SDK example
make example-market-maker         # Run Market Maker SDK example
make example-cross-chain-access   # Run Cross-Chain Access SDK example
make example-errors               # Run error handling example
```

### Code Style & Quality

The project enforces consistent code style:

- **Black**: Code formatting (100 char line length)
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

```bash
# Format code before committing
make format

# Check for issues
make lint
```

### Configuration Files

| File               | Purpose                                      |
| ------------------ | -------------------------------------------- |
| `pyproject.toml`   | Project metadata, dependencies, build config |
| `.env`             | Environment variables (not in git)           |
| `.env.example`     | Template for environment variables           |
| `config.dev.json`  | Development environment addresses            |
| `config.prod.json` | Production environment addresses             |

---

## 🚀 Deployment & CI/CD

### GitHub Actions Workflow

The project uses GitHub Actions for automated publishing to PyPI. The workflow is defined in `.github/workflows/publish.yaml`.

#### Workflow Triggers

| Branch | Action | Destination            |
| ------ | ------ | ---------------------- |
| `main` | Push   | **PyPI** (production)  |
| `test` | Push   | **TestPyPI** (testing) |

#### Workflow Steps

1. **Checkout Code** - Pull latest code from repository
2. **Setup Python** - Install Python 3.11
3. **Install Build Tools** - Install `build` package
4. **Build Package** - Create source distribution and wheel
5. **Publish** - Upload to PyPI or TestPyPI based on branch

```yaml
# Simplified workflow structure
on:
  push:
    branches: [main, test]

jobs:
  build-and-publish:
    - Checkout code
    - Setup Python 3.11
    - Install build backend
    - Build package (python -m build)
    - Publish to TestPyPI (if branch = test)
    - Publish to PyPI (if branch = main)
```

#### Required GitHub Secrets

Configure these secrets in your GitHub repository settings:

| Secret                | Purpose                                |
| --------------------- | -------------------------------------- |
| `PYPI_API_TOKEN_PROD` | PyPI API token for production releases |
| `PYPI_API_TOKEN_TEST` | TestPyPI API token for test releases   |

To get API tokens:

1. **PyPI**: Go to https://pypi.org/manage/account/token/
2. **TestPyPI**: Go to https://test.pypi.org/manage/account/token/

### Manual Deployment

You can also deploy manually using the Makefile:

```bash
# Build distribution packages
make build

# Upload to TestPyPI (testing)
make upload-test

# Upload to PyPI (production)
make upload

# Or use twine directly
pip install twine
python -m build
twine upload dist/*
```

### Version Management

Version is managed in `pyproject.toml`:

```toml
[project]
name = "swarm-collection"
version = "1.0.0b1"  # Update this for new releases
```

**Version Numbering**:

- `1.0.0b1` - Beta release 1
- `1.0.0` - Stable release
- `1.1.0` - Minor version (new features)
- `1.1.1` - Patch version (bug fixes)

### Release Checklist

Before creating a new release:

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` (if exists)
- [ ] Run `make test` to ensure all tests pass
- [ ] Run `make lint` to check code quality
- [ ] Update documentation if needed
- [ ] Commit changes: `git commit -m "Release vX.Y.Z"`
- [ ] Create git tag: `git tag vX.Y.Z`
- [ ] Push to test branch first: `git push origin test`
- [ ] Verify TestPyPI deployment
- [ ] Push to main: `git push origin main`
- [ ] Push tags: `git push --tags`

---

## 📖 Documentation

### Available Documentation

The project includes comprehensive documentation in the `docs/` directory:

#### SDK User Guides (Beginner-Friendly)

- [**Trading SDK User Guide**](docs/trading_sdk_doc.md) - Complete guide to smart routing and unified trading
- [**Market Maker SDK User Guide**](docs/market_maker_sdk_doc.md) - P2P trading and offer creation
- [**Cross-Chain Access SDK User Guide**](docs/cross_chain_access_sdk_doc.md) - Stock market integration

#### API References (Technical)

- [**Trading SDK API Reference**](docs/trading_sdk_api.md) - Detailed method specifications
- [**Market Maker SDK API Reference**](docs/market_maker_sdk_api.md) - RPQ and Web3 client APIs
- [**Cross-Chain Access SDK API Reference**](docs/cross_chain_access_sdk_api.md) - API client specifications

#### Examples

- [**Examples README**](examples/README.md) - Guide to all code examples

### Documentation Structure

Each SDK has two documentation files:

| Type              | Purpose                                             | Audience   |
| ----------------- | --------------------------------------------------- | ---------- |
| **User Guide**    | Setup, concepts, tutorials, troubleshooting         | All users  |
| **API Reference** | Class methods, parameters, return types, exceptions | Developers |

### Quick Links

- **Getting Started**: Start with [Trading SDK User Guide](docs/trading_sdk_doc.md)
- **Advanced Features**: Check individual SDK user guides
- **Technical Details**: Refer to API reference documents
- **Code Examples**: See [examples/](examples/) directory

---

## 💡 Examples

The project includes comprehensive working examples for all SDKs in the `examples/` directory.

### Running Examples

```bash
# Using Makefile (recommended)
make example-trading              # Trading SDK with smart routing
make example-market-maker         # Market Maker P2P trading
make example-cross-chain-access   # Cross-Chain Access stock trading
make example-errors               # Error handling patterns

# Or run directly
python examples/example_trading.py
```

⚠️ **Note**: Examples require a `.env` file with credentials. See [Environment Configuration](#environment-configuration) section.

📖 **Full documentation**: [examples/README.md](examples/README.md)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Workflow

1. **Fork the repository**
2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR_USERNAME/python-swarm-sdks.git
   cd python-swarm-sdks
   ```

3. **Set up development environment**

   ```bash
   make setup
   source venv/bin/activate
   ```

4. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **Make your changes**

   - Write code following project style
   - Add tests for new features
   - Update documentation if needed

6. **Run quality checks**

   ```bash
   make format  # Format code
   make lint    # Check for issues
   make test    # Run tests
   ```

7. **Commit your changes**

   ```bash
   git add .
   git commit -m "Add: your feature description"
   ```

8. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub

### Code Standards

- **Python Version**: 3.8+
- **Code Style**: Black (100 char line length)
- **Import Sorting**: isort
- **Linting**: flake8
- **Type Hints**: mypy

### Commit Message Convention

Use descriptive commit messages:

```
Add: New feature description
Fix: Bug fix description
Update: Changes to existing features
Docs: Documentation updates
Test: Test additions or modifications
Refactor: Code refactoring
Style: Code style changes
```

### Areas for Contribution

- 🐛 **Bug Fixes** - Fix issues reported in GitHub Issues
- ✨ **New Features** - Add new functionality to SDKs
- 📚 **Documentation** - Improve guides and API docs
- 🧪 **Tests** - Increase test coverage
- 🎨 **Examples** - Add more usage examples
- 🔧 **Tooling** - Improve development workflow

### Before Submitting PR

- [ ] Code follows project style (run `make format`)
- [ ] All tests pass (run `make test`)
- [ ] New tests added for new features
- [ ] Documentation updated if needed
- [ ] No linting errors (run `make lint`)
- [ ] Commit messages are clear and descriptive

---

## 🌐 Supported Networks

All SDKs support the following networks:

| Network      | Chain ID |
| ------------ | -------- |
| **Ethereum** | 1        |
| **Polygon**  | 137      |
| **Base**     | 8453     |
| **BSC**      | 56       |

### Network Configuration

Networks are defined in `swarm/shared/models.py`:

```python
from swarm.shared.models import Network

Network.ETHEREUM   # 1
Network.POLYGON    # 137
Network.BASE       # 8453
Network.BSC        # 56
```

RPC endpoints are configured in `swarm/shared/web3/constants.py` and can be overridden with the `rpc_url` parameter when initializing clients.

---

## 🔐 Security

### Best Practices

- ✅ Never commit private keys - use environment variables
- ✅ Verify token addresses before trading
- ✅ Test with small amounts first
- ✅ Use context managers for proper cleanup

### Reporting Security Issues

Email: developers@swarm.com (do NOT create public GitHub issues for vulnerabilities)

---

## ⚠️ Important Caveats

### Decimal Usage (CRITICAL)

- ✅ **Always use `Decimal`** for token amounts - never floats
- ❌ Floats cause precision loss: Use `Decimal("100")` not `100.0`
- ✅ SDKs handle wei conversion automatically

### Async Context Managers Required

All SDK clients must be used with async context managers:

```python
async with TradingClient(...) as client:
    # Use client here
    pass  # Automatic cleanup on exit
```

### Platform-Specific Requirements

- **Market Maker**: Requires RPQ API key for offer discovery
- **Cross-Chain Access**: Requires KYC verification + operates only during market hours (14:30-21:00 UTC, weekdays)
- **Trading SDK**: Benefits from both credentials but can work with just one platform

### Security Warnings

- 🔐 Never commit private keys or `.env` files to version control
- 🔐 Always verify token addresses before trading
- 🔐 Test with small amounts first
- 🔐 Private keys are used locally only - never sent to servers

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

```
Copyright 2025 Swarm

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 🔗 Links & Resources

- **GitHub**: https://github.com/SwarmMarkets/python-swarm-sdks
- **PyPI**: https://pypi.org/project/swarm-collection/
- **Documentation**: [docs/README.md](docs/README.md)
- **Swarm Website**: https://swarm.com

---

## 💬 Support

- 📚 **Documentation**: [docs/](docs/)
- 💡 **Examples**: [examples/](examples/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/SwarmMarkets/python-swarm-sdks/issues)
- 📧 **Email**: developers@swarm.com

---

## 🎉 Acknowledgments

Built by the Swarm Markets team using Web3.py, httpx, and pytest.

---

**Made with ❤️ by Swarm Markets**

_Last Updated: November 21, 2025_
