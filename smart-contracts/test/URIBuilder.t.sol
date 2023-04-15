// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "forge-std/console.sol";
import "../src/URIBuilder.sol";

contract URIBuilderTest is Test {
    URIBuilder public uri_builder;
	function setLayers() public {
	}

    function setUp() public {
        uri_builder = new URIBuilder();
    }

    function testRenderForGas() public {
		uri_builder.buildURI(0, 0, [uint(0), uint(0), uint(0), uint(0)]);
    }

	function testRenderToView() public {
		console.log(
			uri_builder.buildURI(0, 0, [uint(0), uint(0), uint(0), uint(0)])
		);
	}
}
