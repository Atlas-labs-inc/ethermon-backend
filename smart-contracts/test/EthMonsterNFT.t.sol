// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "forge-std/console.sol";
import "../src/EthMonsterNFT.sol";

contract EthMonsterNFTTest is Test {
    EthMonsterNFT public eth_monster_nft;

    function setUp() public {
        eth_monster_nft = new EthMonsterNFT();
		eth_monster_nft.setMintReady(true);
		eth_monster_nft.mint(msg.sender);
	}

	function testTokenUri() public {
		console.log(
			eth_monster_nft.tokenURI(0)
		);
	}
}
