pragma solidity ^0.8.0;
import "openzeppelin-contracts/contracts/utils/Base64.sol";
import "openzeppelin-contracts/contracts/access/Ownable.sol";
import "openzeppelin-contracts/contracts/utils/Strings.sol";

contract URIBuilder is Ownable{
	constructor (){
		// Don't set the deployer contract as the owner
		transferOwnership(tx.origin);
	}

	struct Move {
		string name;
		string ethermon_type;
		uint8 damage;
		uint8 manaCost;
		string buffType;
		uint8 buffAmount;
		string debuffType;
		uint8 debuffAmount;
		uint8 heal;
	}
	// URI Data
	// id => base64 encoded svg
    mapping(uint256 => bytes) public image_map;
	mapping(uint256 => string) public name_map;
	mapping(uint256 => Move) public move_map;
    function setImage(uint layer, bytes memory encoded_svg) external onlyOwner {
        image_map[layer] = encoded_svg;
    }

	function setMove(uint256 id, Move memory move) external onlyOwner {
		move_map[id] = move;
	}

    function buildURI(uint256 token_id, uint256 image_id, uint256[4] memory move_pointers) external view returns (string memory) {
        // Start building the JSON object
		string memory json = string(abi.encodePacked('{"name": "', name_map[image_id], ' #', Strings.toString(token_id), '","description": "An Ethermon NFT", "image": "data:image/svg+xml;base64,', image_map[image_id], '", "attributes": ['));
        // Add attributes for each move
        for (uint i = 0; i < move_pointers.length; i++) {
            Move memory move = move_map[move_pointers[i]];
            json = string(abi.encodePacked(json, '{', 
                '"trait_type": "', move.ethermon_type , '", ',
                '"value": "', move.name, '", ',
                '"damage": ', Strings.toString(move.damage), ', ',
                '"manaCost": ', Strings.toString(move.manaCost), ', ',
                '"buffType": "', move.buffType, '", ',
                '"buffAmount": ', Strings.toString(move.buffAmount), ', ',
                '"debuffType": "', move.debuffType, '", ',
                '"debuffAmount": ', Strings.toString(move.debuffAmount), ', ',
                '"heal": ', Strings.toString(move.heal),
            '}'));
            if (i != move_pointers.length - 1) {
                json = string(abi.encodePacked(json, ','));
            }
        }

        // Close the JSON object and return
        json = string(abi.encodePacked(json, ']}'));
        return json;
    }
}
