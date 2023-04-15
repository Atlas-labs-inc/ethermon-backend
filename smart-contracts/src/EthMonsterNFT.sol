// SPDX-License-Identifier: Unlicense
pragma solidity ^0.8.0;

import "openzeppelin-contracts/contracts/token/ERC721/ERC721.sol";
import "openzeppelin-contracts/contracts/utils/Strings.sol";
import "openzeppelin-contracts/contracts/utils/Counters.sol";
import "openzeppelin-contracts/contracts/utils/Base64.sol";
import "openzeppelin-contracts/contracts/access/Ownable.sol";
import "forge-std/Test.sol";

import "./URIBuilder.sol";
import "./AuctionHouse.sol";

error MintNotReady();
error NonExistentTokenURI();
error NotAuctionHouse();

contract EthMonsterNFT is ERC721, Ownable {
	using Counters for Counters.Counter;
	
	bool public mint_ready;
    Counters.Counter public nextTokenId;
	URIBuilder public uri_builder;
	AuctionHouse public auction_house;


	// tokenId => pseudo-random seed 
	mapping(uint256 => bytes32) public uri_seed_hash;
	
    constructor() ERC721("EthMonsters", "EMS") {
        uri_builder = new URIBuilder();
		auction_house = new AuctionHouse();
    }

	function setMintReady(bool _mint_ready) external onlyOwner {
		mint_ready = _mint_ready;
	}

    function mint(address to) external onlyMintReady {
		uint256 current_token_id = nextTokenId.current();
		bytes32 seed = keccak256(
			abi.encodePacked(
				block.difficulty,
				block.timestamp,
				blockhash(block.number - 1),
				current_token_id,
				tx.origin
			)
		);
        _mint(to, nextTokenId.current());
		uri_seed_hash[current_token_id] = seed;
		nextTokenId.increment();
    }

	function getURIPointersFromSeed(bytes32 seed) private pure returns (uint256, uint256[4] memory) {
		uint256 image_id = uint256(seed) % 135;
		uint256[4] memory move_pointers;
		// TODO:First two are dependent on the type of image
		move_pointers[0] = uint256(keccak256(abi.encodePacked(seed, uint8(0)))) % 100;
		move_pointers[1] = uint256(keccak256(abi.encodePacked(seed, uint8(1)))) % 100;
		// Last two are independent
		move_pointers[2] = uint256(keccak256(abi.encodePacked(seed, uint8(2)))) % 100;
		move_pointers[3] = uint256(keccak256(abi.encodePacked(seed, uint8(3)))) % 100;
		return (image_id, move_pointers);
	}

    function tokenURI(uint256 token_id) public view override onlyMintReady returns (string memory) {
		if (!_exists(token_id)) {
			revert NonExistentTokenURI();
		}
		(uint256 image_id, uint256[4] memory move_pointers) = getURIPointersFromSeed(uri_seed_hash[token_id]);
		return uri_builder.buildURI(token_id, image_id, move_pointers);
	}

	modifier onlyAuctionHouse() {
		if (msg.sender != address(auction_house)) {
			revert NotAuctionHouse();
		}
		_;
	}

	modifier onlyMintReady() {
		if (!mint_ready) {
			revert MintNotReady();
		}
		_;
	}
}
